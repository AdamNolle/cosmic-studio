import bpy, math, random, os, sys
from pathlib import Path
from mathutils import Vector, noise

OUT=Path(os.environ.get('STUDIO_DOCK_OUTPUT', Path(__file__).resolve().parent.parent))
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
RES=int(args[0]) if args else 640
SAMPLES=int(args[1]) if len(args)>1 else 96
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=SAMPLES
scene.cycles.use_denoising=True
scene.cycles.max_bounces=16
scene.cycles.transmission_bounces=12
scene.cycles.transparent_max_bounces=16
scene.cycles.film_transparent_glass=True
scene.cycles.film_transparent_roughness=.2
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices: d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception: pass
scene.render.resolution_x=RES;scene.render.resolution_y=RES
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.image_settings.color_depth='16'
scene.render.film_transparent=True
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.25,.32,.42,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35

def material(name,color,rough=.3,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m,p

glass,p=material('Clear optical glass — thin walls',(.92,.97,1),.065)
p.inputs['Transmission Weight'].default_value=1
p.inputs['IOR'].default_value=1.45
p.inputs['Coat Weight'].default_value=.15
p.inputs['Coat Roughness'].default_value=.045

def revolve(name,profile,mat,segments=192):
    verts=[];faces=[]
    for r,z in profile:
        for i in range(segments):
            a=2*math.pi*i/segments;verts.append((r*math.cos(a),r*math.sin(a),z))
    for j in range(len(profile)-1):
        for i in range(segments):
            a=j*segments+i;b=j*segments+(i+1)%segments
            faces.append((a,b,b+segments,a+segments))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob);ob.data.materials.append(mat)
    for face in mesh.polygons: face.use_smooth=True
    return ob

# Continuous, physically hollow revolved vessel with a rounded rim and bottom.
profile=[(.001,.04),(.65,.04),(.724,.047),(.760,.07),(.783,.10),(.798,.15),(.801,.2),(.979,2.10),(.983,2.135),(.979,2.155),(.969,2.166),(.955,2.168),(.943,2.160),(.937,2.146),(.94,2.126),(.763,.216),(.760,.19),(.752,.17),(.735,.15),(.69,.13),(.001,.13),(.001,.04)]
binob=revolve('Round glass bin · open shell',profile,glass)

# Narrow clear base ring catches a highlight without creating an opaque plinth.
ring=revolve('Polished glass base',[(.768,.088),(.778,.101),(.777,.117),(.766,.13),(.756,.117),(.756,.101),(.768,.088)],glass)

def light(name,loc,energy,size,color,shape='DISK',size_y=None,target=(0,0,1)):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape=shape;data.size=size;data.color=color
    if size_y: data.size_y=size_y
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob
light('Tall left studio strip',(-3,-4,4),650,1.6,(.86,.94,1),'RECTANGLE',5)
light('Right edge strip',(3,-1,3.2),460,.6,(.95,.98,1),'RECTANGLE',4)
light('Top softbox',(-.8,1,6),700,4,(1,.97,.93),'DISK')
light('Rear cyan edge',(2,3,2.6),190,2,(.63,.84,1),'RECTANGLE',3)

def card(name,loc,scale,color,target):
    mat,p=material(name,color,1)
    bpy.ops.mesh.primitive_plane_add(size=2,location=loc)
    ob=bpy.context.object;ob.name=name;ob.scale=scale
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('Z','Y').to_euler()
    ob.data.materials.append(mat);ob.visible_camera=False;ob.visible_shadow=False
    return ob
card('Dark reflection card',(-2.2,-1.4,1.2),(.45,2,1),(.009,.017,.027),(0,0,1))
card('Dark right reflection card',(2.5,1.2,1.1),(.4,2,1),(.025,.04,.06),(0,0,1))

bpy.ops.object.camera_add(location=(0,-8,4.52))
cam=bpy.context.object;cam.name='Icon orthographic camera'
cam.rotation_euler=(Vector((0,0,1.12))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=3.55;scene.camera=cam

papercollection=bpy.data.collections.new('Crumpled paper · full state');scene.collection.children.link(papercollection)
def paper_material(name,tint):
    m,p=material(name,tint,.86)
    nt=m.node_tree
    noiseNode=nt.nodes.new('ShaderNodeTexNoise');noiseNode.inputs['Scale'].default_value=190
    noiseNode.inputs['Detail'].default_value=2
    bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.003
    nt.links.new(noiseNode.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m
papers=[paper_material('Warm white paper',(.93,.918,.88)),paper_material('Bright white paper',(.91,.95,1)),paper_material('Soft white paper',(.98,.975,.96))]

def crumple(name,loc,radius,seed):
    rng=random.Random(seed)
    # A densely creased sheet wrapped almost around itself, with an open seam.
    N=30;M=24;verts=[];faces=[]
    for j in range(M+1):
        v=j/M;phi=.12+(math.pi-.24)*v
        for i in range(N+1):
            u=i/N;theta=2*math.pi*(u*.935+.012)
            q=Vector((math.sin(phi)*math.cos(theta),math.sin(phi)*math.sin(theta),math.cos(phi)))
            sample=q*1.4+Vector((seed*.7,seed*.13,seed*.31))
            n=noise.noise_vector(sample,noise_basis='PERLIN_ORIGINAL')
            folds=(abs(math.sin(theta*2.8+phi*3.5+seed))-.5)*.24
            wrinkles=(abs(math.sin(theta*4.8-phi*3.3+seed*.2))-.5)*.10
            r=radius*(1+.22*n.x+folds+wrinkles)
            # Lift the exposed seam into a paper edge rather than a solid rock.
            seam=max(0,1-min(u,1-u)*15)*(.07+.045*math.sin(phi*8))
            q=q*(r+radius*seam)
            q.z*=.88
            verts.append(q)
    for j in range(M):
        for i in range(N):
            a=j*(N+1)+i;b=a+1;c=b+N+1;d=a+N+1
            if (i+j)%2: faces.extend([(a,b,d),(b,c,d)])
            else: faces.extend([(a,b,c),(a,c,d)])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);papercollection.objects.link(ob)
    ob.location=loc;ob.rotation_euler=tuple(rng.uniform(-math.pi,math.pi) for _ in range(3))
    ob.data.materials.append(papers[seed%len(papers)])
    for face in mesh.polygons:face.use_smooth=False
    solid=ob.modifiers.new('Thin paper edge','SOLIDIFY');solid.thickness=.0016
    return ob

placements=[((-.3,.17,.5),.40,41),((.31,-.17,.58),.40,43),((.25,.24,1.17),.43,51),((-.37,-.16,1.12),.44,54),((-.25,.16,1.73),.46,63),((.39,.04,1.76),.42,65),((-.16,-.19,2.10),.46,72)]
for idx,(loc,r,seed) in enumerate(placements):crumple(f'Crumpled sheet {idx+1:02}',loc,r,seed)

for state in ['trash-empty','trash-full']:
    papercollection.hide_render=state=='trash-empty'
    papercollection.hide_viewport=state=='trash-empty'
    destination=OUT/'png'/str(RES)
    destination.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(destination/f'{state}.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'sources/blender'/f'{state}.blend'))
    bpy.ops.render.render(write_still=True)
print('Glass bin pair complete',RES,SAMPLES)
