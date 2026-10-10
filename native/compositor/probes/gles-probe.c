// SPDX-License-Identifier: GPL-3.0-only
#define _GNU_SOURCE
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES2/gl2.h>
#include <GLES2/gl2ext.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdint.h>
static double now(){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9;}
static GLuint compile(GLenum kind,const char *source){GLuint s=glCreateShader(kind);glShaderSource(s,1,&source,NULL);glCompileShader(s);GLint ok;glGetShaderiv(s,GL_COMPILE_STATUS,&ok);if(!ok){char log[4096];glGetShaderInfoLog(s,sizeof(log),NULL,log);fprintf(stderr,"Compile: %s\n",log);exit(3);}return s;}
static char *load(const char *path){FILE *f=fopen(path,"rb");if(!f)exit(2);fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);char *s=calloc(n+1,1);fread(s,1,n,f);fclose(f);return s;}
int main(int argc,char**argv){
 if(argc!=3)return 2;
 PFNEGLQUERYDEVICESEXTPROC devices=(void*)eglGetProcAddress("eglQueryDevicesEXT");PFNEGLGETPLATFORMDISPLAYEXTPROC platform=(void*)eglGetProcAddress("eglGetPlatformDisplayEXT");EGLDeviceEXT dev[8];EGLint count=0;if(!devices||!platform||!devices(8,dev,&count)||count<1)return 4;
 EGLDisplay display=platform(EGL_PLATFORM_DEVICE_EXT,dev[0],NULL);EGLint major,minor;if(!eglInitialize(display,&major,&minor)){fprintf(stderr,"EGL initialize %x\n",eglGetError());return 4;}
 eglBindAPI(EGL_OPENGL_ES_API);EGLint cfgattrs[]={EGL_SURFACE_TYPE,EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES2_BIT,EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_NONE};EGLConfig config;EGLint n;if(!eglChooseConfig(display,cfgattrs,&config,1,&n)||n<1)return 4;
 EGLint pa[]={EGL_WIDTH,2560,EGL_HEIGHT,640,EGL_NONE};EGLSurface surface=eglCreatePbufferSurface(display,config,pa);EGLint ca[]={EGL_CONTEXT_CLIENT_VERSION,2,EGL_NONE};EGLContext context=eglCreateContext(display,config,EGL_NO_CONTEXT,ca);if(!eglMakeCurrent(display,surface,surface,context))return 4;
 fprintf(stdout,"{\"renderer\":\"%s\",\"version\":\"%s\",\"samples\":[",glGetString(GL_RENDERER),glGetString(GL_VERSION));
 const char *vertex="#version 100\nattribute vec2 position; varying vec2 v_coords;void main(){v_coords=position*0.5+0.5;gl_Position=vec4(position,0.0,1.0);}";
 char *fragment=load(argv[1]);GLuint program=glCreateProgram();glAttachShader(program,compile(GL_VERTEX_SHADER,vertex));glAttachShader(program,compile(GL_FRAGMENT_SHADER,fragment));glBindAttribLocation(program,0,"position");glLinkProgram(program);GLint ok;glGetProgramiv(program,GL_LINK_STATUS,&ok);if(!ok){char log[4096];glGetProgramInfoLog(program,sizeof(log),NULL,log);fprintf(stderr,"Link: %s\n",log);return 5;}glUseProgram(program);
 float positions[]={-1,-1,1,-1,-1,1,1,1};GLuint vbo;glGenBuffers(1,&vbo);glBindBuffer(GL_ARRAY_BUFFER,vbo);glBufferData(GL_ARRAY_BUFFER,sizeof(positions),positions,GL_STATIC_DRAW);glEnableVertexAttribArray(0);glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,0,NULL);
 GLuint texture;glGenTextures(1,&texture);glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,texture);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
 uint8_t *pixels=malloc(2560*96*4);for(int y=0;y<96;y++)for(int x=0;x<2560;x++){int i=(y*2560+x)*4;pixels[i]=(x/28)%2?45:130;pixels[i+1]=50+y;pixels[i+2]=130+x*100/2560;pixels[i+3]=255;}glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,2560,96,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
 float identity[]={1,0,0,0,1,0,0,0,1};glUniform1i(glGetUniformLocation(program,"tex"),0);glUniform1f(glGetUniformLocation(program,"alpha"),1);glUniform4f(glGetUniformLocation(program,"corner_radius"),0,0,0,0);glUniformMatrix3fv(glGetUniformLocation(program,"input_to_geo"),1,GL_FALSE,identity);glUniformMatrix3fv(glGetUniformLocation(program,"geo_to_input"),1,GL_FALSE,identity);glUniform1f(glGetUniformLocation(program,"noise"),.006);
 PFNGLGENQUERIESEXTPROC gen=(void*)eglGetProcAddress("glGenQueriesEXT");PFNGLBEGINQUERYEXTPROC begin=(void*)eglGetProcAddress("glBeginQueryEXT");PFNGLENDQUERYEXTPROC end=(void*)eglGetProcAddress("glEndQueryEXT");PFNGLGETQUERYOBJECTUI64VEXTPROC result=(void*)eglGetProcAddress("glGetQueryObjectui64vEXT");int timer=gen&&begin&&end&&result&&strstr((const char*)glGetString(GL_EXTENSIONS),"GL_EXT_disjoint_timer_query");
 for(int kind=0;kind<4;kind++){
  int w=kind==0?2560:(kind==1?600:(kind==2?420:900)),h=kind==0?32:(kind==1?84:(kind==2?320:620));
  float corner=kind==3?8:6;
  glViewport(0,0,w,h);
  glUniform2f(glGetUniformLocation(program,"geo_size"),w,h);
  glUniform4f(glGetUniformLocation(program,"corner_radius"),corner,corner,corner,corner);
  glUniform1f(glGetUniformLocation(program,"pool_inset"),kind==1?3:0);
  glUniform1f(glGetUniformLocation(program,"pool_radius"),kind==1?3:0);
  glUniform1f(glGetUniformLocation(program,"material_type"),kind);
  for(int i=0;i<50;i++)glDrawArrays(GL_TRIANGLE_STRIP,0,4);glFinish();
  double total=0,min=1e6,max=0,cputotal=0;GLint disjoint=0;for(int batch=0;batch<10;batch++){
   GLuint query=0;if(timer){gen(1,&query);begin(GL_TIME_ELAPSED_EXT,query);}double start=now();for(int i=0;i<300;i++)glDrawArrays(GL_TRIANGLE_STRIP,0,4);if(timer)end(GL_TIME_ELAPSED_EXT);glFinish();double wall=(now()-start)*1000/300;cputotal+=wall;double ms=wall;if(timer){GLuint64EXT ns;result(query,GL_QUERY_RESULT_EXT,&ns);ms=ns/1e6/300;PFNGLDELETEQUERIESEXTPROC del=(void*)eglGetProcAddress("glDeleteQueriesEXT");del(1,&query);glGetIntegerv(GL_GPU_DISJOINT_EXT,&disjoint);if(disjoint){fprintf(stderr,"GPU timer disjoint\n");return 6;}}total+=ms;if(ms<min)min=ms;if(ms>max)max=ms;
  }
  fprintf(stdout,"%s{\"surface\":\"%s\",\"width\":%d,\"height\":%d,\"gpu_timer\":%s,\"mean_ms\":%.6f,\"min_ms\":%.6f,\"max_ms\":%.6f,\"wall_per_draw_ms\":%.6f}",kind?",":"",kind==0?"Panel":(kind==1?"Dock":(kind==2?"Popup":"Window")),w,h,timer?"true":"false",total/10,min,max,cputotal/10);
  if(kind==1){uint8_t *rgb=malloc(w*h*4);glReadPixels(0,0,w,h,GL_RGBA,GL_UNSIGNED_BYTE,rgb);FILE*f=fopen(argv[2],"wb");fprintf(f,"P6\n%d %d\n255\n",w,h);for(int y=h-1;y>=0;y--)for(int x=0;x<w;x++)fwrite(rgb+(y*w+x)*4,1,3,f);fclose(f);free(rgb);}
 }
 fprintf(stdout,"],\"scope\":\"Final material shader only; native blur/capture and full desktop frame times are excluded. 3000 draws per surface, ten GPU query batches.\"}\n");free(pixels);eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,context);eglDestroySurface(display,surface);eglTerminate(display);return glGetError()!=GL_NO_ERROR;
}
