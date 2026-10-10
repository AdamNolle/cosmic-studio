#define _GNU_SOURCE
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <wayland-client.h>
#include "xdg-shell.h"
#include "xdg-decoration.h"
static struct wl_compositor *compositor;
static struct wl_shm *shm;
static struct xdg_wm_base *wm;
static struct zxdg_decoration_manager_v1 *decorations;
static struct wl_surface *surface;
static struct wl_buffer *buffer;
static int buffer_width=560,buffer_height=320;
static int next_width=560,next_height=320;
static uint32_t color;
static int running=1;
static int prepare_buffer(int width,int height){
 if(width<1||height<1||width>8192||height>8192){fprintf(stderr,"Private specimen configure size refused: %dx%d.\n",width,height);return -1;}
 int bytes=width*height*4;
 int fd=memfd_create("studio-ssd-specimen",MFD_CLOEXEC);if(fd<0)return -1;
 if(ftruncate(fd,bytes)){close(fd);return -1;}
 uint32_t *pixels=mmap(NULL,bytes,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
 if(pixels==MAP_FAILED){close(fd);return -1;}
 for(int i=0;i<width*height;i++)pixels[i]=color;
 struct wl_shm_pool *pool=wl_shm_create_pool(shm,fd,bytes);
 struct wl_buffer *replacement=wl_shm_pool_create_buffer(pool,0,width,height,width*4,WL_SHM_FORMAT_ARGB8888);
 wl_shm_pool_destroy(pool);munmap(pixels,bytes);close(fd);
 if(buffer)wl_buffer_destroy(buffer);
 buffer=replacement;buffer_width=width;buffer_height=height;
 return 0;
}
static void ping(void *d,struct xdg_wm_base *w,uint32_t serial){xdg_wm_base_pong(w,serial);}
static const struct xdg_wm_base_listener wm_listener={ping};
static void configure(void *d,struct xdg_surface *s,uint32_t serial){
 xdg_surface_ack_configure(s,serial);
 if(!buffer||buffer_width!=next_width||buffer_height!=next_height){
  if(prepare_buffer(next_width,next_height)){running=0;return;}
 }
 wl_surface_attach(surface,buffer,0,0);
 wl_surface_damage_buffer(surface,0,0,buffer_width,buffer_height);
 wl_surface_commit(surface);
 printf("CONFIGURE=%dx%d\n",buffer_width,buffer_height);fflush(stdout);
}
static const struct xdg_surface_listener surface_listener={configure};
static void size(void *d,struct xdg_toplevel *t,int32_t w,int32_t h,struct wl_array *states){
 next_width=w>0?w:buffer_width;next_height=h>0?h:buffer_height;
 uint32_t *state;int maximized=0,fullscreen=0;
 wl_array_for_each(state,states){maximized|=*state==XDG_TOPLEVEL_STATE_MAXIMIZED;fullscreen|=*state==XDG_TOPLEVEL_STATE_FULLSCREEN;}
 printf("STATE= maximized:%d fullscreen:%d\n",maximized,fullscreen);fflush(stdout);
}
static void close_window(void *d,struct xdg_toplevel *t){running=0;}
static void bounds(void *d,struct xdg_toplevel *t,int32_t w,int32_t h){}
static void capabilities(void *d,struct xdg_toplevel *t,struct wl_array *c){}
static const struct xdg_toplevel_listener toplevel_listener={size,close_window,bounds,capabilities};
static void decoration_configure(void *d,struct zxdg_toplevel_decoration_v1 *t,uint32_t mode){printf("DECORATION_MODE=%s\n",mode==ZXDG_TOPLEVEL_DECORATION_V1_MODE_SERVER_SIDE?"server":"client");fflush(stdout);}
static const struct zxdg_toplevel_decoration_v1_listener decoration_listener={decoration_configure};
static void global(void *d,struct wl_registry *r,uint32_t id,const char *iface,uint32_t version){
 if(!strcmp(iface,"wl_compositor"))compositor=wl_registry_bind(r,id,&wl_compositor_interface,version<4?version:4);
 else if(!strcmp(iface,"wl_shm"))shm=wl_registry_bind(r,id,&wl_shm_interface,1);
 else if(!strcmp(iface,"xdg_wm_base")){wm=wl_registry_bind(r,id,&xdg_wm_base_interface,version<5?version:5);xdg_wm_base_add_listener(wm,&wm_listener,NULL);}
 else if(!strcmp(iface,"zxdg_decoration_manager_v1"))decorations=wl_registry_bind(r,id,&zxdg_decoration_manager_v1_interface,1);
}
static void removed(void *d,struct wl_registry *r,uint32_t id){}
static const struct wl_registry_listener registry_listener={global,removed};
int main(int argc,char **argv){
 const char *runtime=getenv("XDG_RUNTIME_DIR");
 const char *prefix="/home/adamnolle/Documents/Codex/2026-10-10/oka/work/";
 const char *socket=getenv("WAYLAND_DISPLAY");
 char *resolved=runtime?realpath(runtime,NULL):NULL;
 const int private_runtime=resolved&&!strncmp(resolved,prefix,strlen(prefix));free(resolved);
 if(argc!=2 || (strcmp(argv[1],"spotify")&&strcmp(argv[1],"spotify-maximized")&&strcmp(argv[1],"spotify-fullscreen")&&strcmp(argv[1],"light")) || !private_runtime || (socket&&strchr(socket,'/'))){fprintf(stderr,"Use only the task's private runtime and a socket basename with argument spotify, spotify-maximized, spotify-fullscreen or light. Main user runtime is refused.\n");return 2;}
 const int spotify=strcmp(argv[1],"light")!=0;
 color=spotify?0xff121212:0xfff6f4ee;
 struct wl_display *display=wl_display_connect(NULL);if(!display)return 3;
 struct wl_registry *registry=wl_display_get_registry(display);wl_registry_add_listener(registry,&registry_listener,NULL);
 if(wl_display_roundtrip(display)<0||!compositor||!shm||!wm||!decorations){fprintf(stderr,"Missing private native SSD protocol.\n");return 4;}
 surface=wl_compositor_create_surface(compositor);
 struct xdg_surface *xdg=xdg_wm_base_get_xdg_surface(wm,surface);xdg_surface_add_listener(xdg,&surface_listener,NULL);
 struct xdg_toplevel *toplevel=xdg_surface_get_toplevel(xdg);xdg_toplevel_add_listener(toplevel,&toplevel_listener,NULL);
 xdg_toplevel_set_app_id(toplevel,spotify?"spotify":"com.system76.StudioLightSpecimen");
 xdg_toplevel_set_title(toplevel,spotify?"Spotify dark chrome specimen":"Light work app specimen");
 struct zxdg_toplevel_decoration_v1 *decoration=zxdg_decoration_manager_v1_get_toplevel_decoration(decorations,toplevel);zxdg_toplevel_decoration_v1_add_listener(decoration,&decoration_listener,NULL);zxdg_toplevel_decoration_v1_set_mode(decoration,ZXDG_TOPLEVEL_DECORATION_V1_MODE_SERVER_SIDE);
 if(!strcmp(argv[1],"spotify-maximized"))xdg_toplevel_set_maximized(toplevel);
 if(!strcmp(argv[1],"spotify-fullscreen"))xdg_toplevel_set_fullscreen(toplevel,NULL);
 printf("REQUESTED_MODE=%s\n",argv[1]);fflush(stdout);
 wl_surface_commit(surface);
 while(running&&wl_display_dispatch(display)>=0){}
 zxdg_toplevel_decoration_v1_destroy(decoration);xdg_toplevel_destroy(toplevel);xdg_surface_destroy(xdg);wl_surface_destroy(surface);if(buffer)wl_buffer_destroy(buffer);wl_display_disconnect(display);return 0;
}
