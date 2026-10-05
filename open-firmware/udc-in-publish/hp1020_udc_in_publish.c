/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_udc_in_publish.h"

#define IN_CTL 0x020u
#define IN_FIFO 0x028u
#define IN_MPS 0x02cu
#define IN_DESPTR 0x034u
#define DEVCTL 0x404u
#define DEVSTS 0x408u
#define IRQ_MASK 0x418u

static bool in_pub_same(struct hp1020_tusb_cookie a,struct hp1020_tusb_cookie b) {
    return a.id==b.id && a.epoch==b.epoch && a.generation==b.generation &&
        a.sequence==b.sequence && a.endpoint==b.endpoint;
}
static bool in_pub_valid(const struct hp1020_udc_in_publish *p) {
    return p && p->initialized && p->port && p->port->initialized && p->port->adapter;
}
static enum hp1020_udc_in_publish_result in_pub_leave(struct hp1020_udc_in_publish *p,
    enum hp1020_udc_in_publish_result r) { p->busy=0;return r; }
static enum hp1020_udc_in_publish_result in_pub_fail(struct hp1020_udc_in_publish *p,
    struct hp1020_tusb_cookie c,uint8_t step) {
    p->failed=1;p->failure_cookie=c;p->failure_step=step;
    const struct hp1020_udc_in_observation fault={.cookie=c,.endpoint_fault=0x80000401u};
    (void)hp1020_udc_in_observe(p->port,&fault,(struct hp1020_udc_in_completion_facts){0});
    return in_pub_leave(p,HP1020_IN_PUBLISH_FAULT);
}
enum hp1020_udc_in_publish_result hp1020_udc_in_publish_init(
    struct hp1020_udc_in_publish *p,struct hp1020_udc_in *port,
    const struct hp1020_udc_in_publish_io *io) {
    if(!p || p->initialized || !port || !port->initialized ||
        port->phase!=HP1020_UDC_IN_FREE || !io || !io->ready || !io->read32 ||
        !io->write32 || !io->order || !io->visible)return HP1020_IN_PUBLISH_INVALID;
    *p=(struct hp1020_udc_in_publish){.port=port,.io=*io,.initialized=1};
    return HP1020_IN_PUBLISH_OK;
}
enum hp1020_udc_in_publish_result hp1020_udc_in_publish_packet(
    struct hp1020_udc_in_publish *p,struct hp1020_tusb_cookie c,
    struct hp1020_udc_in_publish_facts_ext f) {
    if(!in_pub_valid(p))return HP1020_IN_PUBLISH_INVALID;
    if(p->busy)return HP1020_IN_PUBLISH_WAIT;
    if(p->failed)return HP1020_IN_PUBLISH_FAULT;
    struct hp1020_udc_in *port=p->port;
    if(!c.id || port->phase==HP1020_UDC_IN_FREE || !in_pub_same(c,port->cookie))
        return HP1020_IN_PUBLISH_STALE;
    const uint8_t facts[5]={f.mode_packet64_be,f.tx_idle_fifo_empty,f.mapping_cache_lease,
        f.register_window_stable,f.cnak_window_safe};
    for(unsigned i=0;i<5;i++)if(facts[i]>1)return HP1020_IN_PUBLISH_INVALID;
    for(unsigned i=0;i<4;i++)if(!facts[i])return HP1020_IN_PUBLISH_WAIT;
    const struct hp1020_tusb_adapter *a=port->adapter;
    const struct hp1020_tusb_owner *owner=&a->owners[3];
    if(port->busy || port->phase!=HP1020_UDC_IN_PREPARED || port->cancel_requested || port->fault_reason ||
        a->busy || a->stack_active || a->exhausted || !a->opened || a->programming_dirty ||
        a->printer->reset_active || a->binding_pending_epoch ||
        (a->pending_kind && a->pending_destructive) || !tud_ready() ||
        a->transport_epoch!=c.epoch || a->active_transport_epoch!=c.epoch ||
        a->printer->document->receive.generation!=c.generation ||
        owner->state!=HP1020_TUSB_OWNER_DCD || !in_pub_same(c,owner->cookie) ||
        owner->cancel_requested || owner->packet_fault)return HP1020_IN_PUBLISH_WAIT;
    p->busy=1;
    if(!p->io.ready(p->io.context,c))return in_pub_leave(p,HP1020_IN_PUBLISH_WAIT);
    uint32_t v,ctl,mask;
#define READ(offset,dest) do { if(!p->io.read32(p->io.context,(offset),&(dest))) \
    return in_pub_leave(p,HP1020_IN_PUBLISH_READ_ERROR); } while(0)
#define REQUIRE(condition) do { if(!(condition))return in_pub_leave(p,HP1020_IN_PUBLISH_WAIT); } while(0)
    READ(DEVCTL,v);
    /* Packet64/BE, transmit DMA enabled; RX DMA may independently be active.
     * Reject buffer-fill/descriptor-update/threshold, disconnect, global NAK
     * and pending commands. Unlike the OUT arm path, do not require RDE=0. */
    REQUIRE((v&0x228u)==0x228u && !(v&0xfcd3u));
    READ(IN_CTL,ctl);REQUIRE(ctl==0x20u || ctl==0x60u);
    READ(IN_MPS,v);REQUIRE((v&0xffffu)==64);
    READ(IN_FIFO,v);REQUIRE((v&0xffffu)>=16);
    READ(IRQ_MASK,mask);
    if(ctl&0x40u) {
        REQUIRE(f.cnak_window_safe);
        READ(DEVSTS,v);REQUIRE(v&0x8000u);
    }
#undef READ
#undef REQUIRE
#define STEP(condition,id) do { if(!(condition))return in_pub_fail(p,c,(id)); } while(0)
#define WRITE(offset,value,id) STEP(p->io.write32(p->io.context,(offset),(value)),(id))
#define ORDER(id) STEP(p->io.order(p->io.context),(id))
    STEP(p->io.visible(p->io.context,port->packet),HP1020_IN_PACKET_VISIBLE);
    STEP(p->io.visible(p->io.context,port->descriptor),HP1020_IN_DESCRIPTOR_VISIBLE);
    ORDER(HP1020_IN_MEMORY_ORDER);
    struct hp1020_udc_in_submission proposal;
    STEP(hp1020_udc_in_take_submission(port,c,(struct hp1020_udc_in_publish_facts){1,1,1},
        &proposal)==HP1020_UDC_IN_OK,HP1020_IN_TAKE);
    WRITE(IN_DESPTR,proposal.descriptor.dma,HP1020_IN_DESPTR);
    ORDER(HP1020_IN_DESPTR_ORDER);
    WRITE(IRQ_MASK,mask&~2u,HP1020_IN_IRQ_MASK);
    ORDER(HP1020_IN_IRQ_ORDER);
    if(ctl&0x40u) {
        WRITE(IN_CTL,0x120u,HP1020_IN_CNAK);
        ORDER(HP1020_IN_CNAK_ORDER);
        STEP(p->io.read32(p->io.context,IN_CTL,&v) && v==0x20u,HP1020_IN_NAK_READ);
    }
    WRITE(IN_CTL,0x28u,HP1020_IN_POLL);
    ORDER(HP1020_IN_POLL_ORDER);
#undef STEP
#undef WRITE
#undef ORDER
    return in_pub_leave(p,HP1020_IN_PUBLISH_OK);
}
enum hp1020_udc_in_publish_result hp1020_udc_in_publish_clear(
    struct hp1020_udc_in_publish *p,struct hp1020_tusb_cookie c,uint8_t clean) {
    if(!in_pub_valid(p) || clean>1)return HP1020_IN_PUBLISH_INVALID;
    if(p->busy)return HP1020_IN_PUBLISH_WAIT;
    if(!p->failed || !in_pub_same(c,p->failure_cookie))return HP1020_IN_PUBLISH_STALE;
    const struct hp1020_tusb_adapter *a=p->port->adapter;
    if(!clean || p->port->busy || p->port->phase!=HP1020_UDC_IN_FREE ||
        a->busy || a->stack_active || a->owners[3].state || a->in_prepared ||
        a->in_result_pending || a->delivering_live)return HP1020_IN_PUBLISH_WAIT;
    p->failed=0;return HP1020_IN_PUBLISH_OK;
}
