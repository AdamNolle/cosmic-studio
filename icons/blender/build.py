"""Blender 4 material studies; run with blender -b --python build.py.
Actual geometry, PBR materials and studio lighting. No image-generation service.
"""
import bpy, math, os, json, sys
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

def srgb(h):
 vals=[int(h[i:i+2],16)/255 for i in (1,3,5)]
 return tuple(v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in vals)+(1,)
def material(name,color,metal=0,rough=.25,coat=.3,grain=.035):
 m=bpy.data.materials.new(name);m.diffuse_color=srgb(color);m.use_nodes=True
 n=m.node_tree.nodes;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=srgb(color);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.14
 if grain:
  noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=340;noise.inputs['Detail'].default_value=2
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=grain;bump.inputs['Distance'].default_value=.0007;m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
 return m
M={
'edge':material('Anodized midnight · fine bead-blast','#293747',.8,.3,.25,.13),
'base':material('Midnight enamel · satin grain','#152B46',.1,.24,.8,.12),
'ghost':material('Glazed porcelain · ivory','#EBF4F7',0,.30,.45,.02),
'ink':material('Recessed blue graphite','#16334D',0,.45,.05,.01),
'orange':material('Brave · orange lacquer','#E94808',0,.36,.3,.025),
'white':material('Pearl white enamel','#FFF9F2',0,.36,.25,.01),
'black':material('Lens barrel · anodized aluminum','#141C27',.8,.27,.4,.15),
'silver':material('Machined iris center','#C9D5DC',.8,.22,.45,.05),
}
def poly(name,points,mat,z,depth=.06,bevel=.025):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='2D';c.resolution_u=12;c.fill_mode='BOTH';c.extrude=depth;c.bevel_depth=bevel;c.bevel_resolution=4
 if isinstance(points[0][0],(float,int)):points=[points]
 for loop in points:
  s=c.splines.new('POLY');s.points.add(len(loop)-1)
  for p,(x,y) in zip(s.points,loop):p.co=(x,y,0,1)
  s.use_cyclic_u=True
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.location.z=z;o.data.materials.append(mat);return o

def rounded(size=3.86,r=.76):
 # Continuous superellipse curvature avoids a hard straight-to-arc join.
 a=size/2;power=2/4.35;points=[]
 for i in range(192):
  t=2*math.pi*i/192;c=math.cos(t);s=math.sin(t)
  points.append((a*math.copysign(abs(c)**power,c),a*math.copysign(abs(s)**power,s)))
 return points


def base(color='#397DB8'):
 M['base']=material('Soft satin ceramic '+color,color,0,.32,.55,.035)
 poly('Soft ceramic edge',rounded(3.90,.81),M['base'],0,.04,.08)
 poly('Satin glass enamel face',rounded(3.88,.79),M['base'],.10,.06,.07)

def line(name,pts,r,mat,z):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=12;c.bevel_depth=r;c.bevel_resolution=5;s=c.splines.new('POLY');s.points.add(len(pts)-1)
 for p,(x,y) in zip(s.points,pts):p.co=(x,y,z,1)
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(mat)
 for x,y in (pts[0],pts[-1]):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=r,location=(x,y,z));bpy.context.object.data.materials.append(mat)

def cylinder(name,r,depth,z,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=r,depth=depth,location=(0,0,z));o=bpy.context.object;o.name=name;o.data.materials.append(mat)
 mod=o.modifiers.new('Precision bevel','BEVEL');mod.width=.025;mod.segments=4;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 for p in o.data.polygons:p.use_smooth=True
 return o

def ghost():
 base()
 # Terminal prompt silhouette, with softly rounded lower scallops.
 pts=[(-.83,-.86),(-.83,.34)]
 for i in range(49):
  a=math.pi-i*math.pi/48;pts.append((.83*math.cos(a),.34+.83*math.sin(a)))
 pts +=[(.83,-.86),(.42,-.62),(0,-.89),(-.42,-.62)]
 poly('Ghostty · porcelain ghost',pts,M['ghost'],.295,.025,.095)
 line('Prompt chevron',[(-.48,.47),(-.2,.25),(-.48,.03)],.044,M['ink'],.412)
 line('Prompt underscore',[(.03,.025),(.42,.025)],.044,M['ink'],.412)
 # Crisp inset seam around the material housing provides depth at dock size.


def darktable():
 base('#26354B');cylinder('Aperture housing',1.48,.07,.28,M['black']);cylinder('Aperture inset',1.38,.025,.33,M['ink'])
 colors=['#FFCF16','#F57816','#D8133C','#B12EB7','#2085DF','#58AB28']
 for i,col in enumerate(colors):
  mat=material('Darktable blade '+str(i+1),col,.05,.36,.35,.025)
  a=math.radians(i*60+6);b=a+math.radians(55)
  pts=[(1.33*math.cos(a+(b-a)*j/24),1.33*math.sin(a+(b-a)*j/24)) for j in range(25)]
  c=a+math.radians(117);pts.append((.43*math.cos(c),.43*math.sin(c)))
  poly('Lacquered aperture blade '+str(i+1),pts,mat,.37,.018,.026)
 cylinder('Iris center / turned aluminum',.185,.035,.402,M['silver'])


def simplify(points,eps=.016):
 if len(points)<3:return points
 a,b=Vector(points[0]),Vector(points[-1]);delta=b-a
 distances=[abs(delta.x*(a.y-y)-(a.x-x)*delta.y)/max(delta.length,1e-9) for x,y in points]
 index=max(range(len(points)),key=distances.__getitem__)
 if distances[index]<=eps:return [points[0],points[-1]]
 return simplify(points[:index+1],eps)[:-1]+simplify(points[index:],eps)

def clean_loop(points):
 # Split a closed contour at its farthest point before open-path simplification.
 a=points[0];k=max(range(len(points)),key=lambda i:(points[i][0]-a[0])**2+(points[i][1]-a[1])**2)
 return simplify(points[:k+1])[:-1]+simplify(points[k:]+[points[0]])[:-1]

def mask_loops(image,predicate):
 w,h=image.size;pix=list(image.pixels);cells=set()
 for y in range(h):
  for x in range(w):
   rgba=pix[(y*w+x)*4:(y*w+x)*4+4]
   if predicate(rgba):cells.add((x,y))
 edges={}
 for x,y in cells:
  for neighbour,a,b in [((x,y-1),(x,y),(x+1,y)),((x+1,y),(x+1,y),(x+1,y+1)),((x,y+1),(x+1,y+1),(x,y+1)),((x-1,y),(x,y+1),(x,y))]:
   if neighbour not in cells:edges.setdefault(a,[]).append(b)
 loops=[]
 while edges:
  start=next(iter(edges));p=start;loop=[]
  while True:
   loop.append(p);options=edges[p];q=options.pop()
   if not options:del edges[p]
   p=q
   if p==start:break
   if p not in edges:break
  if len(loop)>12:
   # Retain exact silhouette; remove only collinear pixel-edge vertices.
   clean=[loop[i] for i in range(len(loop)) if (loop[i][0]-loop[i-1][0])*(loop[(i+1)%len(loop)][1]-loop[i][1])!=(loop[i][1]-loop[i-1][1])*(loop[(i+1)%len(loop)][0]-loop[i][0])]
   loops.append(clean_loop([((x/w-.5)*2.9,(y/h-.5)*2.9) for x,y in clean]))
 return loops

def brave():
 base('#EDE4D8')
 if Path('/usr/share/blender/scripts/addons/io_curve_svg').exists():sys.path.append('/usr/share/blender/scripts/addons')
 bpy.ops.preferences.addon_enable(module='io_curve_svg')
 before=set(bpy.data.objects)
 bpy.ops.import_curve.svg(filepath=str(ROOT/'sources/brave.svg'))
 marks=[o for o in bpy.data.objects if o not in before and o.type=='CURVE']
 bpy.context.view_layer.update()
 vertices=[o.matrix_world @ Vector(v) for o in marks for v in o.bound_box]
 lo=Vector(tuple(min(v[i] for v in vertices) for i in range(3)));hi=Vector(tuple(max(v[i] for v in vertices) for i in range(3)));center=(lo+hi)/2
 scale=2.75/max(hi.x-lo.x,hi.y-lo.y)
 for o in marks:
  col=o.data.materials[0].diffuse_color if o.data.materials and o.data.materials[0] else (0,0,0,1)
  white=min(col[:3])>.7
  o.matrix_world=Matrix.Translation((0,0,.345 if white else .29)) @ Matrix.Diagonal((scale,scale,scale,1)) @ Matrix.Translation(-center) @ o.matrix_world
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  for spline in o.data.splines:
   for point in list(spline.bezier_points)+list(spline.points):point.radius=1
  o.data.extrude=.005 if white else .032;o.data.bevel_depth=.006 if white else .025;o.data.bevel_resolution=4;o.data.resolution_u=24;o.data.materials.clear();o.data.materials.append(M['white'] if white else M['orange'])
  o.name='Brave · original vector '+('face' if white else 'lion')
  bpy.context.view_layer.update()
  assert max(o.dimensions)<3.5, 'Unexpected SVG scale or bevel radius'


def light(name,location,power,size,color=(1,1,1),shape='DISK',size_y=None):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape=shape;data.size=size;data.color=color
 if size_y is not None:data.size_y=size_y
 ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.location=location;ob.rotation_euler=(Vector((0,0,.1))-ob.location).to_track_quat('-Z','Y').to_euler()

def stage(scene):
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=96;scene.cycles.use_denoising=True;scene.cycles.adaptive_threshold=.025
 scene.render.threads_mode='FIXED';scene.render.threads=8;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
 scene.world=bpy.data.worlds.new('Neutral studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.19,.24,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
 scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
 light('Large cool softbox',(-3,-1,6),320,5.0,(.86,.93,1))
 light('Long reflection card',(2,3,5),260,5.0,(1,.91,.78),'RECTANGLE',3.0)
 light('Edge fill',(-4,4,2),120,4.0,(.55,.72,1))
 camera=bpy.data.cameras.new('Icon camera');cam=bpy.data.objects.new('Icon camera',camera);bpy.context.collection.objects.link(cam);cam.location=(0,-.65,11);cam.rotation_euler=(Vector((0,0,.16))-cam.location).to_track_quat('-Z','Y').to_euler();camera.type='ORTHO';camera.ortho_scale=4.9;camera.lens=55;scene.camera=cam

for name,make in [('Ghostty',ghost),('Darktable',darktable),('Brave',brave)]:
 scene=bpy.data.scenes.new(name+' · material study');bpy.context.window.scene=scene;stage(scene);make();scene.render.filepath=str(ROOT/(name.lower()+'.png'))
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'studio-material-studies.blend'))
 bpy.ops.render.render(write_still=True)
# Preserve all three scenes and packed resources in one editable project.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'studio-material-studies.blend'))
print('Rendered three material studies; previous desktop icon theme remains active.')
