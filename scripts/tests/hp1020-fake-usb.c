/* Offline scheduler fixture. Implements CUPS fd 3/4 only; no USB APIs. */
#include <cups/sidechannel.h>
#include <arpa/inet.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#ifndef TEST_ROOT
#error Compile with an isolated TEST_ROOT
#endif
static void event(const char *kind,const char *job,unsigned pages) {
    FILE *file=fopen(TEST_ROOT "/tmp/events","a");
    if(!file) exit(90);
    fprintf(file,"%s %s %u %u %d\n",kind,job,pages,getuid(),getpid()); fclose(file);
}
static void response(const char *kind,const char *token,unsigned pages) {
    char buf[256];
    int n=snprintf(buf,sizeof(buf),"@PJL USTATUS JOB\r\n%s\r\nNAME=\"%s\"\r\nPAGES=%u\r\n\f",kind,token,pages);
    for(int i=0;i<n;i+=7) if(write(3,buf+i,n-i<7?n-i:7)<0) exit(91);
}
int main(int argc,char **argv) {
    if(argc<6) return 1;
    signal(SIGTERM,SIG_IGN); signal(SIGPIPE,SIG_IGN);
    const char *job=argv[1];
    event("open",job,0);
    fprintf(stderr,"STATE: -connecting-to-device\n");
    char data[1024*1024], token[64]=""; size_t used=0;
    unsigned pages=0; int received=0,completed=0;
    for(;;) {
        struct pollfd fds[]={{0,POLLIN,0},{4,POLLIN,0}};
        if(poll(fds,2,50)<0) continue;
        if(fds[1].revents&POLLIN) {
            char payload[8192]; int length=sizeof(payload); cups_sc_command_t cmd; cups_sc_status_t state;
            if(cupsSideChannelRead(&cmd,&state,payload,&length,1)) return 3;
            if(cmd==CUPS_SC_CMD_GET_DEVICE_ID) {
                const char *id="MFG:Hewlett-Packard;MDL:HP LaserJet 1020;FWVER:fixture;";
                cupsSideChannelWrite(cmd,CUPS_SC_STATUS_OK,id,strlen(id),1);
            } else if(cmd==CUPS_SC_CMD_SOFT_RESET) {
                event("reset",job,0); cupsSideChannelWrite(cmd,CUPS_SC_STATUS_OK,NULL,0,1);
            } else {
                char yes=1; cupsSideChannelWrite(cmd,CUPS_SC_STATUS_OK,&yes,1,1);
            }
        }
        if(fds[0].revents&(POLLIN|POLLHUP)) {
            if(used==sizeof(data)-1) return 4;
            ssize_t n=read(0,data+used,sizeof(data)-used-1);
            if(n==0) {event("closed",job,pages);return 0;}
            if(n<0) continue;
            used+=n; data[used]=0;
            char mode[32]="ok"; FILE *file=fopen(TEST_ROOT "/tmp/mode","r");
            if(file) {fgets(mode,sizeof(mode),file);fclose(file);}
            if(!strncmp(mode,"fail",4)) {event("failure",job,0);return 7;}
            if(!*token) {
                const char *a=strstr(data,"@PJL JOB NAME=\"");
                if(a) {a+=15;const char *b=strchr(a,'"');if(b && b-a<63){memcpy(token,a,b-a);response("START",token,0);}}
            }
            if(!received && used>=9 && !memcmp(data+used-9,"\033%-12345X",9)) {
                const char *j=NULL;
                for(size_t i=0;i+4<used;i++) if(!memcmp(data+i,"JZJZ",4)){j=data+i+4;break;}
                if(j) {
                    size_t pos=j-data; int ended=0;
                    while(pos+16<=used){uint32_t size,kind;memcpy(&size,data+pos,4);memcpy(&kind,data+pos+4,4);size=ntohl(size);kind=ntohl(kind);if(size<16||pos+size>used)break;if(kind==2)pages++;pos+=size;if(kind==1){ended=1;break;}}
                    if(ended) {
                        received=1;event("received",job,pages);
                        char filename[1024];snprintf(filename,sizeof(filename),TEST_ROOT "/tmp/job-%s.zjs",job);
                        file=fopen(filename,"wb");if(!file)return 5;fwrite(data,1,used,file);fclose(file);
                        if(!strncmp(mode,"paper",5)) {
                            const char *out="@PJL USTATUS DEVICE\r\nCODE=41001\r\nONLINE=FALSE\r\n\f";
                            write(3,out,strlen(out));
                        } else {response("END",token,pages);completed=1;}
                    } else pages=0;
                }
            }
        }
        if(received && !completed && access(TEST_ROOT "/tmp/release",F_OK)==0) {
            const char *out="@PJL INFO STATUS\r\nCODE=10001\r\n\f";
            write(3,out,strlen(out)); response("END",token,pages); completed=1;
        }
    }
}
