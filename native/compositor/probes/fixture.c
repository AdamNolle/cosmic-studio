// SPDX-License-Identifier: GPL-3.0-only
#define _GNU_SOURCE
#include <wayland-client.h>
#include "layer-shell.h"
#include "background-effect.h"
#include <sys/mman.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <poll.h>
#include <time.h>

static struct wl_compositor *compositor;
static struct wl_shm *shm;
static struct zwlr_layer_shell_v1 *layers;
static struct ext_background_effect_manager_v1 *effects;
static struct wl_display *display;
struct Surface {
 struct wl_surface *surface;
 struct zwlr_layer_surface_v1 *layer;
 struct ext_background_effect_surface_v1 *effect;
 struct wl_buffer *buffers[2];
 uint32_t *pixels[2];
 int width,height,kind,busy[2],current,configured;
};
static struct Surface surfaces[3];
static void release(void *data,struct wl_buffer *buffer) {
 struct Surface *s=data;for(int i=0;i<2;i++)if(s->buffers[i]==buffer)s->busy[i]=0;
}
static const struct wl_buffer_listener buffer_listener={release};
static uint32_t color(int r,int g,int b,int a){return ((uint32_t)a<<24)|((r*a/255)<<16)|((g*a/255)<<8)|(b*a/255);}
static void fill(struct Surface *s,int index,int tick){
 for(int y=0;y<s->height;y++)for(int x=0;x<s->width;x++){
  uint32_t c;
  if(s->kind==0){
   int stripe=((x+tick*3)/28)%2;
   c=color(40+(x*140/s->width),50+(y*120/s->height),stripe?130:200,255);
   if(((x/64)+(y/64))%2)c=color(180,130,80,255);
  }else{
   c=color(5,10,19,42);
   if(x<3||y<3||x>=s->width-3||y>=s->height-3)c=color(160,190,230,180);
   if(s->kind==2){
    int pos=(x-22)%64;
    if(x>=22&&x<s->width-20&&y>=18&&y<62&&pos>=0&&pos<44)
     c=color(80+((x/64)*30)%170,145,220,255);
   }else if(y>=9&&y<22&&x>=22&&x<150)c=color(220,228,245,255);
  }
  s->pixels[index][y*s->width+x]=c;
 }
}
static void make_buffers(struct Surface *s){
 int size=s->width*s->height*4;
 for(int i=0;i<2;i++){
  int fd=memfd_create("cosmic-glass-fixture",MFD_CLOEXEC);if(fd<0)abort();
  if(ftruncate(fd,size)<0)abort();
  s->pixels[i]=mmap(NULL,size,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
  struct wl_shm_pool *pool=wl_shm_create_pool(shm,fd,size);
  s->buffers[i]=wl_shm_pool_create_buffer(pool,0,s->width,s->height,s->width*4,WL_SHM_FORMAT_ARGB8888);
  wl_buffer_add_listener(s->buffers[i],&buffer_listener,s);wl_shm_pool_destroy(pool);close(fd);
 }
}
static void configure(void *data,struct zwlr_layer_surface_v1 *layer,uint32_t serial,uint32_t width,uint32_t height){
 struct Surface *s=data;fprintf(stderr,"configure kind=%d width=%u height=%u\n",s->kind,width,height);zwlr_layer_surface_v1_ack_configure(layer,serial);
 if(!s->configured){
  s->width=width?width:s->width;s->height=height?height:s->height;make_buffers(s);
  if(s->effect){struct wl_region *region=wl_compositor_create_region(compositor);wl_region_add(region,0,0,s->width,s->height);ext_background_effect_surface_v1_set_blur_region(s->effect,region);wl_region_destroy(region);}
  fill(s,0,0);s->busy[0]=1;wl_surface_attach(s->surface,s->buffers[0],0,0);wl_surface_damage_buffer(s->surface,0,0,s->width,s->height);wl_surface_commit(s->surface);s->configured=1;
 }
}
static void closed(void *data,struct zwlr_layer_surface_v1 *layer){fprintf(stderr,"closed kind=%d\n",((struct Surface*)data)->kind);(void)layer;}
static const struct zwlr_layer_surface_v1_listener layer_listener={configure,closed};
static void capabilities(void *data,struct ext_background_effect_manager_v1 *manager,uint32_t flags){(void)data;(void)manager;(void)flags;}
static const struct ext_background_effect_manager_v1_listener effect_listener={capabilities};
static void global(void *data,struct wl_registry *registry,uint32_t name,const char *interface,uint32_t version){
 (void)data;
 if(!strcmp(interface,"wl_compositor"))compositor=wl_registry_bind(registry,name,&wl_compositor_interface,version<4?version:4);
 if(!strcmp(interface,"wl_shm"))shm=wl_registry_bind(registry,name,&wl_shm_interface,1);
 if(!strcmp(interface,"zwlr_layer_shell_v1"))layers=wl_registry_bind(registry,name,&zwlr_layer_shell_v1_interface,1);
 if(!strcmp(interface,"ext_background_effect_manager_v1")){effects=wl_registry_bind(registry,name,&ext_background_effect_manager_v1_interface,1);ext_background_effect_manager_v1_add_listener(effects,&effect_listener,NULL);}
}
static void remove_global(void *d,struct wl_registry *r,uint32_t n){(void)d;(void)r;(void)n;}
static const struct wl_registry_listener registry_listener={global,remove_global};
int main(){
 if(!getenv("STUDIO_PRIVATE_TEST")||strcmp(getenv("STUDIO_PRIVATE_TEST"),"1")){fprintf(stderr,"Use run-isolated.py for this probe.\n");return 5;}
 display=wl_display_connect(NULL);if(!display)return 2;
 struct wl_registry *registry=wl_display_get_registry(display);wl_registry_add_listener(registry,&registry_listener,NULL);wl_display_roundtrip(display);wl_display_roundtrip(display);
 if(!compositor||!shm||!layers||!effects){fprintf(stderr,"Required native protocols unavailable\n");return 3;}
 const char *names[]={"StudioFixtureBackground","Panel","Dock"};
 int count=getenv("STUDIO_FIXTURE_BACKGROUND_ONLY")?1:3;
 for(int i=0;i<count;i++){
  struct Surface *s=&surfaces[i];s->kind=i;s->width=i==2?430:0;s->height=i==0?0:(i==1?32:84);s->surface=wl_compositor_create_surface(compositor);
  s->layer=zwlr_layer_shell_v1_get_layer_surface(layers,s->surface,NULL,i==0?ZWLR_LAYER_SHELL_V1_LAYER_BACKGROUND:ZWLR_LAYER_SHELL_V1_LAYER_TOP,names[i]);
  zwlr_layer_surface_v1_add_listener(s->layer,&layer_listener,s);
  zwlr_layer_surface_v1_set_size(s->layer,s->width,s->height);
  uint32_t anchor=i==0?15:(i==1?ZWLR_LAYER_SURFACE_V1_ANCHOR_TOP|ZWLR_LAYER_SURFACE_V1_ANCHOR_LEFT|ZWLR_LAYER_SURFACE_V1_ANCHOR_RIGHT:ZWLR_LAYER_SURFACE_V1_ANCHOR_BOTTOM);
  zwlr_layer_surface_v1_set_anchor(s->layer,anchor);zwlr_layer_surface_v1_set_exclusive_zone(s->layer,-1);
  if(i==2)zwlr_layer_surface_v1_set_margin(s->layer,0,0,24,0);
  if(i>0)s->effect=ext_background_effect_manager_v1_get_background_effect(effects,s->surface);
  wl_surface_commit(s->surface);
 }
 for(int n=0;n<3;n++)wl_display_roundtrip(display);
 fprintf(stdout,"Native layer fixture: Panel+Dock, ext_background_effect_v1, SHM buffers ready\n");fflush(stdout);
 int tick=0;int ticks=getenv("STUDIO_FIXTURE_BACKGROUND_ONLY")?2400:200;for(int n=0;n<ticks;n++){
  wl_display_dispatch_pending(display);wl_display_flush(display);
  struct pollfd p={wl_display_get_fd(display),POLLIN,0};poll(&p,1,25);if(p.revents&POLLIN){if(wl_display_dispatch(display)<0)break;}
  if(getenv("STUDIO_FIXTURE_ANIMATE")&&n%4==0){struct Surface *s=&surfaces[0];int next=1-s->current;if(s->configured&&!s->busy[next]){fill(s,next,++tick);s->busy[next]=1;s->current=next;wl_surface_attach(s->surface,s->buffers[next],0,0);wl_surface_damage_buffer(s->surface,0,0,s->width,s->height);wl_surface_commit(s->surface);}}
 }
 wl_display_disconnect(display);return 0;
}
