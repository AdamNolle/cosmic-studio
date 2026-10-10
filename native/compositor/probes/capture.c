// SPDX-License-Identifier: GPL-3.0-only
#define _GNU_SOURCE
#include <wayland-client.h>
#include "image-source.h"
#include "image-copy.h"
#include <sys/mman.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <poll.h>
#include <time.h>
static struct wl_display *display;
static struct wl_shm *shm;
static struct wl_output *output;
static struct ext_output_image_capture_source_manager_v1 *sources;
static struct ext_image_copy_capture_manager_v1 *copies;
static uint32_t *pixels,width,height,format=WL_SHM_FORMAT_XBGR8888;
static uint32_t buffer_transform;
static int finished=0,result=3;
static const char *filename;
static void transformed(void*d,struct ext_image_copy_capture_frame_v1*f,uint32_t t){(void)d;(void)f;buffer_transform=t;fprintf(stderr,"capture transform=%u\n",t);}
static void damaged(void*d,struct ext_image_copy_capture_frame_v1*f,int32_t x,int32_t y,int32_t w,int32_t h){(void)d;(void)f;(void)x;(void)y;(void)w;(void)h;}
static void presented(void*d,struct ext_image_copy_capture_frame_v1*f,uint32_t hi,uint32_t lo,uint32_t n){(void)d;(void)f;(void)hi;(void)lo;(void)n;}
static void ready(void*d,struct ext_image_copy_capture_frame_v1*f){
 (void)d;(void)f;FILE *out=fopen(filename,"wb");if(!out){finished=1;return;}
 uint32_t ow=(buffer_transform&1)?height:width,oh=(buffer_transform&1)?width:height;
 fprintf(out,"P6\n%u %u\n255\n",ow,oh);
 for(uint32_t y=0;y<oh;y++)for(uint32_t x=0;x<ow;x++){
  uint32_t sx=x,sy=y;
  switch(buffer_transform){
   case WL_OUTPUT_TRANSFORM_90:sx=width-1-y;sy=x;break;
   case WL_OUTPUT_TRANSFORM_180:sx=width-1-x;sy=height-1-y;break;
   case WL_OUTPUT_TRANSFORM_270:sx=y;sy=height-1-x;break;
   case WL_OUTPUT_TRANSFORM_FLIPPED:sx=width-1-x;break;
   case WL_OUTPUT_TRANSFORM_FLIPPED_90:sx=y;sy=x;break;
   case WL_OUTPUT_TRANSFORM_FLIPPED_180:sy=height-1-y;break;
   case WL_OUTPUT_TRANSFORM_FLIPPED_270:sx=width-1-y;sy=height-1-x;break;
  }
  uint32_t pixel=pixels[sy*width+sx];unsigned char p[3]={pixel,pixel>>8,pixel>>16};fwrite(p,1,3,out);
 }
 fclose(out);
 fprintf(stderr,"Captured native %ux%u oriented frame\n",ow,oh);finished=1;result=0;
}
static void failed(void*d,struct ext_image_copy_capture_frame_v1*f,uint32_t r){(void)d;(void)f;fprintf(stderr,"Capture failed reason=%u\n",r);finished=1;}
static const struct ext_image_copy_capture_frame_v1_listener frame_listener={transformed,damaged,presented,ready,failed};
static void buffer_size(void*d,struct ext_image_copy_capture_session_v1*s,uint32_t w,uint32_t h){(void)d;(void)s;width=w;height=h;}
static void shm_format(void*d,struct ext_image_copy_capture_session_v1*s,uint32_t f){(void)d;(void)s;if(f==WL_SHM_FORMAT_XBGR8888||f==WL_SHM_FORMAT_ABGR8888)format=f;}
static void dmabuf_device(void*d,struct ext_image_copy_capture_session_v1*s,struct wl_array*a){(void)d;(void)s;(void)a;}
static void dmabuf_format(void*d,struct ext_image_copy_capture_session_v1*s,uint32_t f,struct wl_array*a){(void)d;(void)s;(void)f;(void)a;}
static void done(void*d,struct ext_image_copy_capture_session_v1*s){
 (void)d;if(!width||!height)return;int size=width*height*4;int fd=memfd_create("studio-private-capture",MFD_CLOEXEC);if(fd<0||ftruncate(fd,size)<0)abort();pixels=mmap(NULL,size,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
 struct wl_shm_pool *pool=wl_shm_create_pool(shm,fd,size);struct wl_buffer *buffer=wl_shm_pool_create_buffer(pool,0,width,height,width*4,format);wl_shm_pool_destroy(pool);close(fd);
 struct ext_image_copy_capture_frame_v1 *frame=ext_image_copy_capture_session_v1_create_frame(s);ext_image_copy_capture_frame_v1_add_listener(frame,&frame_listener,NULL);ext_image_copy_capture_frame_v1_attach_buffer(frame,buffer);ext_image_copy_capture_frame_v1_damage_buffer(frame,0,0,width,height);ext_image_copy_capture_frame_v1_capture(frame);
}
static void stopped(void*d,struct ext_image_copy_capture_session_v1*s){(void)d;(void)s;fprintf(stderr,"Native capture stopped\n");finished=1;}
static const struct ext_image_copy_capture_session_v1_listener session_listener={buffer_size,shm_format,dmabuf_device,dmabuf_format,done,stopped};
static void global(void*d,struct wl_registry*r,uint32_t n,const char*i,uint32_t v){(void)d;(void)v;
 if(!strcmp(i,"wl_shm"))shm=wl_registry_bind(r,n,&wl_shm_interface,1);
 if(!strcmp(i,"wl_output")&&!output)output=wl_registry_bind(r,n,&wl_output_interface,1);
 if(!strcmp(i,"ext_output_image_capture_source_manager_v1"))sources=wl_registry_bind(r,n,&ext_output_image_capture_source_manager_v1_interface,1);
 if(!strcmp(i,"ext_image_copy_capture_manager_v1"))copies=wl_registry_bind(r,n,&ext_image_copy_capture_manager_v1_interface,1);
}
static void removed(void*d,struct wl_registry*r,uint32_t n){(void)d;(void)r;(void)n;}
static const struct wl_registry_listener registry_listener={global,removed};
int main(int argc,char **argv){if(!getenv("STUDIO_PRIVATE_TEST")||strcmp(getenv("STUDIO_PRIVATE_TEST"),"1"))return 5;if(argc!=2)return 2;filename=argv[1];display=wl_display_connect(NULL);if(!display)return 2;struct wl_registry *registry=wl_display_get_registry(display);wl_registry_add_listener(registry,&registry_listener,NULL);wl_display_roundtrip(display);
 if(!shm||!output||!sources||!copies){fprintf(stderr,"Capture protocols unavailable\n");return 4;}
 struct ext_image_capture_source_v1 *source=ext_output_image_capture_source_manager_v1_create_source(sources,output);struct ext_image_copy_capture_session_v1 *session=ext_image_copy_capture_manager_v1_create_session(copies,source,0);ext_image_copy_capture_session_v1_add_listener(session,&session_listener,NULL);
 for(int i=0;i<240&&!finished;i++){wl_display_dispatch_pending(display);wl_display_flush(display);struct pollfd p={wl_display_get_fd(display),POLLIN,0};poll(&p,1,25);if(p.revents&POLLIN&&wl_display_dispatch(display)<0)break;}
 wl_display_disconnect(display);return result;
}
