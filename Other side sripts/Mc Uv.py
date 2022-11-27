import maya.cmds as cmds

def uvfix(faces):

	cmds.progressWindow(title="MC UV",status="Uving " + str(faces),progress=0,ii=False)

	Mesh=faces
	MeshFace = cmds.polyListComponentConversion(Mesh,tf=True)
	MeshFace = cmds.filterExpand(MeshFace, sm=34)
	Div = len(MeshFace)
	f = 0
	cmds.polyMapCut(MeshFace,ch=True)
	for i1 in range(len(MeshFace)):
		MeshUv = cmds.polyListComponentConversion(MeshFace[i1],ff=True,tuv=True)
		MeshUv = cmds.filterExpand(MeshUv, sm=35)
		loca=[0,0]
		for i in range(len(MeshUv)):
			loc=cmds.polyEditUV(MeshUv[i],q=True,u=1,v=1)
			loca[0]=loca[0] + loc[0]
			loca[1]=loca[1] + loc[1]

		f = f + 1
		cmds.progressWindow(edit=True,progress=f/Div*100)
		loca[0]=loca[0] / 4
		loca[1]=loca[1] / 4
		cmds.polyEditUV(MeshFace[i1],pv=loca[1], sv=0.5, su=0.5, pu=loca[0])
	cmds.pause(seconds=0.5)
	cmds.progressWindow(ep=True)

for i in cmds.ls(sl=True):
	uvfix(i)