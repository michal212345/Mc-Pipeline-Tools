import maya.cmds as cmds
import maya.mel as mel

def Clearnamespace():
    cmds.namespace(setNamespace=':')
    Namespace = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)

    Remove = ['MergeWithFlagTempNamespaceName','UI','shared']

    for i in Remove:
        try:
            Namespace.remove(i)
        except:
            print("Skipped: " + i)

    for Name in Namespace:
        mel.eval('namespace -mergeNamespaceWithRoot -removeNamespace ' + Name + ';')
try:
    Clearnamespace()
except:
    cmds.error("No names spaces that can be removed.")