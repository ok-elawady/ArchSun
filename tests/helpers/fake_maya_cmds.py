import sys
import types


class FakeMayaCmds:
    def __init__(self):
        self.plugins_loaded = {"mtoa": False}
        self.nodes = {}
        self.attrs = {}
        self.connections = set()
        self.undo_chunks = []
        self.ignore_light_name = False
        self._name_counters = {}

    def pluginInfo(self, plugin_name, query=False, loaded=False):
        if query and loaded:
            return self.plugins_loaded.get(plugin_name, False)
        raise NotImplementedError("FakeMayaCmds only supports query=True, loaded=True")

    def loadPlugin(self, plugin_name, quiet=False):
        self.plugins_loaded[plugin_name] = True
        return plugin_name

    def undoInfo(self, openChunk=False, closeChunk=False):
        if openChunk:
            self.undo_chunks.append("open")
        if closeChunk:
            self.undo_chunks.append("close")

    def group(self, em=False, name=None):
        if not em:
            raise NotImplementedError("FakeMayaCmds only supports empty group creation")
        self._create_node(name, "transform")
        return name

    def shadingNode(self, node_type, asLight=False, asTexture=False, name=None):
        if asLight:
            if self.ignore_light_name:
                transform_name = self._next_generated_name("transform")
            else:
                transform_name = name

            shape_name = f"{transform_name}Shape"
            self._create_node(transform_name, "transform")
            self._create_node(shape_name, node_type)
            self.nodes[transform_name]["shapes"] = [shape_name]
            self.nodes[shape_name]["parent"] = transform_name
            return transform_name

        if asTexture:
            self._create_node(name, node_type)
            return name

        raise NotImplementedError("Unsupported shadingNode configuration")

    def parent(self, child, parent_group):
        child = self._normalize_node_name(child)
        parent_group = self._normalize_node_name(parent_group)
        child_node = self.nodes[child]
        old_parent = child_node["parent"]

        if old_parent and child in self.nodes[old_parent]["children"]:
            self.nodes[old_parent]["children"].remove(child)

        child_node["parent"] = parent_group
        if child not in self.nodes[parent_group]["children"]:
            self.nodes[parent_group]["children"].append(child)

        return [child]

    def rename(self, old_name, new_name):
        old_name = self._normalize_node_name(old_name)
        new_name = self._normalize_node_name(new_name)
        if old_name == new_name:
            return new_name
        if new_name in self.nodes:
            raise ValueError(f"Node '{new_name}' already exists")

        node = self.nodes.pop(old_name)
        self.nodes[new_name] = node

        if node["type"] == "transform":
            parent_name = node["parent"]
            if parent_name:
                self.nodes[parent_name]["children"] = [
                    new_name if child == old_name else child
                    for child in self.nodes[parent_name]["children"]
                ]

            renamed_shapes = []
            for shape_name in list(node["shapes"]):
                new_shape_name = shape_name
                if shape_name == f"{old_name}Shape":
                    new_shape_name = f"{new_name}Shape"
                    if new_shape_name in self.nodes:
                        raise ValueError(f"Node '{new_shape_name}' already exists")
                    shape_node = self.nodes.pop(shape_name)
                    self.nodes[new_shape_name] = shape_node
                else:
                    shape_node = self.nodes[shape_name]

                shape_node["parent"] = new_name
                renamed_shapes.append(new_shape_name)

            node["shapes"] = renamed_shapes
            return new_name

        parent_name = node["parent"]
        if parent_name:
            self.nodes[parent_name]["shapes"] = [
                new_name if shape == old_name else shape
                for shape in self.nodes[parent_name]["shapes"]
            ]

        return new_name

    def objExists(self, name):
        return self._normalize_node_name(name) in self.nodes

    def listRelatives(
        self, node_name, children=False, shapes=False, parent=False, fullPath=False
    ):
        node_name = self._normalize_node_name(node_name)
        if node_name not in self.nodes:
            return []

        node = self.nodes[node_name]

        if children:
            children_names = list(node["children"])
            if fullPath:
                return [self._full_path(child_name) for child_name in children_names]
            return children_names
        if shapes:
            shape_names = list(node["shapes"])
            if fullPath:
                return [self._full_path(shape_name) for shape_name in shape_names]
            return shape_names
        if parent:
            if not node["parent"]:
                return []
            if fullPath:
                return [self._full_path(node["parent"])]
            return [node["parent"]]

        return []

    def nodeType(self, node_name):
        return self.nodes[self._normalize_node_name(node_name)]["type"]

    def isConnected(self, source_attr, destination_attr):
        return (source_attr, destination_attr) in self.connections

    def connectAttr(self, source_attr, destination_attr, force=False):
        self.connections.add((source_attr, destination_attr))

    def setAttr(self, attr_name, value):
        self.attrs[attr_name] = value

    def get_attr(self, attr_name):
        if attr_name in self.attrs:
            return self.attrs.get(attr_name)

        normalized_attr = self._normalize_attr_name(attr_name)
        for stored_attr, value in self.attrs.items():
            if self._normalize_attr_name(stored_attr) == normalized_attr:
                return value

        return None

    def _create_node(self, name, node_type):
        self.nodes[name] = {
            "type": node_type,
            "parent": None,
            "children": [],
            "shapes": [],
        }

    def _next_generated_name(self, base_name):
        current = self._name_counters.get(base_name, 0) + 1
        self._name_counters[base_name] = current
        return f"{base_name}{current}"

    def _normalize_node_name(self, name):
        return name.split("|")[-1]

    def _normalize_attr_name(self, attr_name):
        node_name, separator, attribute_name = attr_name.partition(".")
        normalized_node_name = self._normalize_node_name(node_name)
        if not separator:
            return normalized_node_name
        return f"{normalized_node_name}.{attribute_name}"

    def _full_path(self, node_name):
        parent_name = self.nodes[node_name]["parent"]
        if not parent_name:
            return f"|{node_name}"
        return f"{self._full_path(parent_name)}|{node_name}"


def install_fake_maya(
    monkeypatch,
    include_ui=False,
    main_window_ptr=1001,
    control_ptrs=None,
):
    fake_cmds = FakeMayaCmds()
    control_ptrs = control_ptrs or {}

    maya_module = types.ModuleType("maya")
    cmds_module = types.ModuleType("maya.cmds")

    exported_names = (
        "pluginInfo",
        "loadPlugin",
        "undoInfo",
        "group",
        "shadingNode",
        "parent",
        "rename",
        "objExists",
        "listRelatives",
        "nodeType",
        "isConnected",
        "connectAttr",
        "setAttr",
    )

    for name in exported_names:
        setattr(cmds_module, name, getattr(fake_cmds, name))

    cmds_module._state = fake_cmds
    maya_module.cmds = cmds_module

    monkeypatch.setitem(sys.modules, "maya", maya_module)
    monkeypatch.setitem(sys.modules, "maya.cmds", cmds_module)

    if include_ui:
        omui_module = types.ModuleType("maya.OpenMayaUI")

        class FakeMQtUtil:
            @staticmethod
            def mainWindow():
                return main_window_ptr

            @staticmethod
            def findControl(control_name):
                return control_ptrs.get(control_name)

        omui_module.MQtUtil = FakeMQtUtil
        maya_module.OpenMayaUI = omui_module
        monkeypatch.setitem(sys.modules, "maya.OpenMayaUI", omui_module)

    return fake_cmds
