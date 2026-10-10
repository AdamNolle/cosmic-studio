"""Offline optical glass app icons, editable Blender 5 scenes, no renderer at runtime."""
from pathlib import Path
import argparse, bpy, json, math, sys
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser();p.add_argument('--only',nargs='*');p.add_argument('--append',action='store_true');p.add_argument('--samples',type=int,default=48);p.add_argument('--resolution',type=int,default=768);a=p.parse_args(args)
family=json.loads((ROOT/'sources/family.local.json').read_text())
if a.only:family=[r for r in family if r['id'] in a.only]
if a.append:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'studio-glass-family.blend'))
 for row in family:
  for scene in list(bpy.data.scenes):
   if scene.name.startswith(row['name']+' · Studio Glass'):bpy.data.scenes.remove(scene)
 bpy.ops.outliner.orphans_purge(do_recursive=True)

def color(hex):
 rgb=[int(hex[i:i+2],16)/255 for i in (1,3,5)]
 return tuple(v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in rgb)+(1,)

def material(name,hex,rough=.24,transmission=0,metal=0,coat=.5):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=color(hex);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.12;p.inputs['Transmission Weight'].default_value=transmission;p.inputs['IOR'].default_value=1.46
 return m

def outline(size,shape):
 power=1 if shape=='circle' else 2/4.8; r=size/2
 return [(r*math.copysign(abs(math.cos(t))**power,math.cos(t)),r*math.copysign(abs(math.sin(t))**power,math.sin(t))) for t in [2*math.pi*i/256 for i in range(256)]]

def poly(name,loops,mat,z,depth,bevel):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='2D';c.resolution_u=16;c.fill_mode='BOTH';c.extrude=depth;c.bevel_depth=bevel;c.bevel_resolution=5
 if isinstance(loops[0][0],(float,int)):loops=[loops]
 for points in loops:
  s=c.splines.new('POLY');s.points.add(len(points)-1)
  for q,(x,y) in zip(s.points,points):q.co=(x,y,0,1)
  s.use_cyclic_u=True
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.location.z=z;o.data.materials.append(mat);return o

def optical_shell(shape,mat):
 # A shallow biconvex cast-glass slab is a volume, not a gradient stroke. The
 # changing surface normals concentrate the white card reflection near a corner.
 contour=outline(3.88,shape);segments=len(contour);rings=24
 verts=[(0,0,.16)];faces=[]
 for ring in range(1,rings+1):
  radius=ring/rings;z=.075+.085*(1-radius*radius)
  verts.extend((x*radius,y*radius,z) for x,y in contour)
 for j in range(segments):faces.append((0,1+j,1+(j+1)%segments))
 for ring in range(1,rings):
  lo=1+(ring-1)*segments;hi=lo+segments
  for j in range(segments):k=(j+1)%segments;faces.append((lo+j,hi+j,hi+k,lo+k))
 bottom=len(verts);verts.extend((x,y,-.04) for x,y in contour);top=1+(rings-1)*segments
 for j in range(segments):k=(j+1)%segments;faces.append((top+j,bottom+j,bottom+k,top+k))
 faces.append(tuple(reversed(range(bottom,bottom+segments))))
 mesh=bpy.data.meshes.new('Continuous polished glass volume');mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new('Shallow optical glass shell · physical thickness',mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(mat)
 for face in mesh.polygons:face.use_smooth=True
 bevel=obj.modifiers.new('Soft cast-glass boundary','BEVEL');bevel.width=.035;bevel.segments=5
 return obj

def simplify(points,eps=.008):
 if len(points)<3:return points
 x,y=points[0];xx,yy=points[-1];dx,dy=xx-x,yy-y;l=math.hypot(dx,dy)
 distances=[abs(dx*(y-v)-(x-u)*dy)/max(l,1e-9) for u,v in points];i=max(range(len(points)),key=distances.__getitem__)
 if distances[i]<=eps:return [points[0],points[-1]]
 return simplify(points[:i+1],eps)[:-1]+simplify(points[i:],eps)

def silhouette(image):
 # Derive relief from alpha, preserving all app-specific silhouettes and holes.
 w,h=image.size; pix=list(image.pixels); cells={(x,y) for y in range(h) for x in range(w) if pix[(y*w+x)*4+3]>.45}; edges={}
 for x,y in cells:
  for n,aa,bb in [((x,y-1),(x,y),(x+1,y)),((x+1,y),(x+1,y),(x+1,y+1)),((x,y+1),(x+1,y+1),(x,y+1)),((x-1,y),(x,y+1),(x,y))]:
   if n not in cells:edges.setdefault(aa,[]).append(bb)
 loops=[]
 while edges:
  start=next(iter(edges));pt=start;loop=[]
  while True:
   loop.append(pt);opts=edges[pt];q=opts.pop()
   if not opts:del edges[pt]
   pt=q
   if pt==start or pt not in edges:break
  if len(loop)<14:continue
  points=[((x/w-.5)*2.68,(y/h-.5)*2.68) for x,y in loop]
  k=max(range(len(points)),key=lambda i:(points[i][0]-points[0][0])**2+(points[i][1]-points[0][1])**2)
  reduced=simplify(points[:k+1])[:-1]+simplify(points[k:]+[points[0]])[:-1]
  if len(reduced)>3:loops.append(reduced)
 return loops

def light(name,loc,power,size,col,shape='DISK',sy=None):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape=shape;data.size=size;data.color=col
 if sy:data.size_y=sy
 ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,.1))-ob.location).to_track_quat('-Z','Y').to_euler()

def setup(scene):
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=a.samples;scene.cycles.use_denoising=True;scene.cycles.adaptive_threshold=.03;scene.cycles.max_bounces=8;scene.cycles.transmission_bounces=6
 scene.render.threads_mode='FIXED';scene.render.threads=8;scene.render.resolution_x=a.resolution;scene.render.resolution_y=a.resolution;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
 scene.world=bpy.data.worlds.new('Soft cool-white optical studio');scene.world.use_nodes=True;bg=scene.world.node_tree.nodes['Background'];bg.inputs[0].default_value=(.22,.27,.34,1);bg.inputs[1].default_value=.45
 scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
 light('Large diffuse identity fill',(-3,3,6),260,4.2,(.87,.95,1))
 light('Concentrated upper-left white reflection',(-1.4,2.8,6),270,2.2,(1,.97,.93),'RECTANGLE',.42)
 light('Opposing lower-right blue edge',(3,-3,3),170,2.5,(.5,.79,1),'RECTANGLE',.36)
 light('Gentle warm side fill',(4,2,5),90,3.2,(1,.91,.82))
 camera=bpy.data.cameras.new('Near-front app identity camera');cam=bpy.data.objects.new(camera.name,camera);bpy.context.collection.objects.link(cam);cam.location=(0,-.72,11);cam.rotation_euler=(Vector((0,0,.1))-cam.location).to_track_quat('-Z','Y').to_euler();camera.type='ORTHO';camera.ortho_scale=4.85;scene.camera=cam

def build(row):
 core=material('Pigmented optical substrate '+row['top'],row['top'],rough=.27,metal=0,coat=.2)
 # Pigment varies through the depth of each object rather than dulling every
 # application's palette with a uniform gray translucent cap.
 nodes=core.node_tree.nodes;bs=nodes.get('Principled BSDF');coords=nodes.new('ShaderNodeTexCoord');split=nodes.new('ShaderNodeSeparateXYZ');ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=color(row['base']);ramp.color_ramp.elements[1].color=color(row['top']);ramp.color_ramp.elements[1].position=.86
 core.node_tree.links.new(coords.outputs['Generated'],split.inputs['Vector']);core.node_tree.links.new(split.outputs['Y'],ramp.inputs['Fac']);core.node_tree.links.new(ramp.outputs['Color'],bs.inputs['Base Color']);core.node_tree.links.new(ramp.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.14
 clear=material('Polished cast optical glass · IOR 1.46','#ffffff',rough=.025,transmission=1,coat=0)
 poly('Continuous-curvature pigmented backing',outline(3.72,row['shape']),core,-.065,.022,.065)
 optical_shell(row['shape'],clear)
 # Brand artwork is physically raised with a bevel; the alpha image gives exact
 # original colors while the rear relief casts a material contact shadow.
 image=bpy.data.images.load(row['mark'],check_existing=True);image.colorspace_settings.name='sRGB';image.pack()
 relief=material('App identity relief '+row['name'],row['mark_color'],rough=.25,metal=.08,coat=.55)
 loops=silhouette(image)
 if loops:poly('Identifying silhouette · beveled material relief',loops,relief,.26,.035,.026)
 m=bpy.data.materials.new('Original mark surface '+row['name']);m.use_nodes=True;n=m.node_tree.nodes;bs=n.get('Principled BSDF');bs.inputs['Roughness'].default_value=.28;bs.inputs['Coat Weight'].default_value=.5;bs.inputs['Coat Roughness'].default_value=.16
 tex=n.new('ShaderNodeTexImage');tex.image=image;m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);m.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
 bpy.ops.mesh.primitive_plane_add(size=2.68,location=(0,0,.322));o=bpy.context.object;o.name='Faithful brand colors / original metaphor';o.data.materials.append(m)
 # Very thin optical glaze over the identity strengthens edge depth. No noisy
 # procedural grain: the small icon retains a clean identifying shape.

for row in family:
 scene=bpy.data.scenes.new(row['name']+' · Studio Glass');bpy.context.window.scene=scene;setup(scene);build(row);scene.render.filepath=row['render'];bpy.ops.render.render(write_still=True);print('Rendered '+row['name'],flush=True)
if len(bpy.data.scenes)>1 and 'Scene' in bpy.data.scenes:bpy.data.scenes.remove(bpy.data.scenes['Scene'])
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/('studio-glass-candidates.blend' if a.only and not a.append else 'studio-glass-family.blend')))
print('Saved editable glass geometry, materials, packed app artwork, lighting and scenes.',flush=True)
