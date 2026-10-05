/* SPDX-License-Identifier: GPL-2.0-or-later
 * Bounded bulk-IN staging, following the existing EP0 ownership contract.
 */
#include "hp1020_udc_in.h"
#include <string.h>

static uint32_t be32(const uint8_t *p) {
    return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3];
}
static void put_be32(uint8_t *p,uint32_t v) {
    p[0]=(uint8_t)(v>>24);p[1]=(uint8_t)(v>>16);p[2]=(uint8_t)(v>>8);p[3]=(uint8_t)v;
}
static bool range(const void *p,uintptr_t n) { return p && n && (uintptr_t)p<=UINTPTR_MAX-(n-1); }
static bool overlap(const void *a,uintptr_t an,const void *b,uintptr_t bn) {
    return (uintptr_t)a<=(uintptr_t)b+bn-1 && (uintptr_t)b<=(uintptr_t)a+an-1;
}
static bool span(struct hp1020_udc_in_span p,uint32_t n) {
    return p.bytes==n && range(p.cpu,p.bytes) && !((uintptr_t)p.cpu&15u) &&
        p.dma && !(p.dma&15u) && p.dma<=UINT32_MAX-(p.bytes-1);
}
static bool same(struct hp1020_tusb_cookie a,struct hp1020_tusb_cookie b) {
    return a.id==b.id && a.epoch==b.epoch && a.generation==b.generation &&
        a.sequence==b.sequence && a.endpoint==b.endpoint;
}
static enum hp1020_udc_in_result enter(struct hp1020_udc_in *s) {
    if(!s || !s->initialized || !s->adapter)return HP1020_UDC_IN_INVALID;
    if(s->busy)return HP1020_UDC_IN_WAIT;
    s->busy=1;return HP1020_UDC_IN_OK;
}
static enum hp1020_udc_in_result leave(struct hp1020_udc_in *s,enum hp1020_udc_in_result r) {
    s->busy=0;return r;
}
static bool current(const struct hp1020_udc_in *s,struct hp1020_tusb_cookie c) {
    return s->phase!=HP1020_UDC_IN_FREE && c.id && same(s->cookie,c);
}
static void retire(struct hp1020_udc_in *s) {
    /* Neither allocation is erased, including after cancellation. */
    s->cookie=(struct hp1020_tusb_cookie){0};s->original=NULL;s->length=0;
    s->phase=HP1020_UDC_IN_FREE;s->cancel_requested=s->fault_reported=0;s->fault_reason=0;
}
static enum hp1020_udc_in_result fault(struct hp1020_udc_in *s) {
    s->cancel_requested=1;
    if(s->fault_reported)return HP1020_UDC_IN_FAULT;
    s->last_adapter_result=hp1020_tusb_adapter_packet_fault(s->adapter,s->cookie,s->fault_reason);
    if(s->last_adapter_result==HP1020_TUSB_WAIT)return HP1020_UDC_IN_WAIT;
    if(s->last_adapter_result!=HP1020_TUSB_OK && s->last_adapter_result!=HP1020_TUSB_STALE)
        return HP1020_UDC_IN_ADAPTER_ERROR;
    s->fault_reported=1;return HP1020_UDC_IN_FAULT;
}
enum hp1020_udc_in_result hp1020_udc_in_init(struct hp1020_udc_in *s,
    struct hp1020_tusb_adapter *a,struct hp1020_udc_in_span d,struct hp1020_udc_in_span p) {
    if(!range(s,sizeof(*s)) || !range(a,sizeof(*a)) || !a->initialized ||
        a->config.ep_in!=0x81 || s->initialized || !span(d,16) || !span(p,64) ||
        overlap(s,sizeof(*s),a,sizeof(*a)) || overlap(d.cpu,16,p.cpu,64) ||
        (d.dma<=p.dma+63u && p.dma<=d.dma+15u))return HP1020_UDC_IN_INVALID;
    if(overlap(s,sizeof(*s),d.cpu,16) || overlap(s,sizeof(*s),p.cpu,64) ||
        overlap(a,sizeof(*a),d.cpu,16) || overlap(a,sizeof(*a),p.cpu,64))return HP1020_UDC_IN_INVALID;
    memset(s,0,sizeof(*s));s->adapter=a;s->descriptor=d;s->packet=p;s->initialized=1;
    return HP1020_UDC_IN_OK;
}
enum hp1020_udc_in_result hp1020_udc_in_prepare(struct hp1020_udc_in *s,
    uint8_t endpoint,uint8_t *source,uint16_t length,struct hp1020_tusb_cookie *cookie) {
    enum hp1020_udc_in_result r=enter(s);if(r)return r;
    if(endpoint!=0x81 || !cookie || length>64 || (length && !range(source,length)) ||
        (!length && source))return leave(s,HP1020_UDC_IN_INVALID);
    if(s->phase!=HP1020_UDC_IN_FREE)return leave(s,HP1020_UDC_IN_WAIT);
    if(length && (overlap(source,length,s,sizeof(*s)) || overlap(source,length,s->adapter,sizeof(*s->adapter)) ||
        overlap(source,length,s->descriptor.cpu,16) || overlap(source,length,s->packet.cpu,64)))
        return leave(s,HP1020_UDC_IN_INVALID);
    struct hp1020_tusb_cookie c={0};
    s->last_adapter_result=hp1020_tusb_adapter_bind_submission(s->adapter,endpoint,source,length,&c);
    if(s->last_adapter_result!=HP1020_TUSB_OK)return leave(s,HP1020_UDC_IN_ADAPTER_ERROR);
    /* No fallible work follows binding. All later failures retain both sources. */
    s->cookie=c;s->original=source;s->length=length;s->phase=HP1020_UDC_IN_PREPARED;
    s->cancel_requested=s->fault_reported=0;s->fault_reason=0;
    if(length)memcpy(s->packet.cpu,source,length);
    put_be32(s->descriptor.cpu+4,0);put_be32(s->descriptor.cpu+8,s->packet.dma);
    put_be32(s->descriptor.cpu+12,0);put_be32(s->descriptor.cpu,UINT32_C(0x08000000)|length);
    *cookie=c;return leave(s,HP1020_UDC_IN_OK);
}
enum hp1020_udc_in_result hp1020_udc_in_take_submission(struct hp1020_udc_in *s,
    struct hp1020_tusb_cookie c,struct hp1020_udc_in_publish_facts f,struct hp1020_udc_in_submission *out) {
    enum hp1020_udc_in_result r=enter(s);if(r)return r;
    if(!current(s,c))return leave(s,HP1020_UDC_IN_STALE);
    if(!out || f.mode_packet64_be>1 || f.descriptor_visible>1 || f.packet_visible>1)
        return leave(s,HP1020_UDC_IN_INVALID);
    if(s->phase!=HP1020_UDC_IN_PREPARED || s->cancel_requested || s->fault_reason ||
        !f.mode_packet64_be || !f.descriptor_visible || !f.packet_visible)
        return leave(s,HP1020_UDC_IN_WAIT);
    const struct hp1020_tusb_adapter *a=s->adapter;
    const struct hp1020_tusb_owner *owner=&a->owners[3];
    if(a->exhausted || a->transport_epoch!=c.epoch || a->active_transport_epoch!=c.epoch ||
        a->printer->document->receive.generation!=c.generation ||
        owner->state!=HP1020_TUSB_OWNER_DCD || !same(owner->cookie,c) ||
        owner->cancel_requested || owner->packet_fault)
        return leave(s,HP1020_UDC_IN_WAIT);
    *out=(struct hp1020_udc_in_submission){s->cookie,s->descriptor,s->packet,s->original,s->length};
    s->phase=HP1020_UDC_IN_EXPOSED;return leave(s,HP1020_UDC_IN_OK);
}
enum hp1020_udc_in_result hp1020_udc_in_observe(struct hp1020_udc_in *s,
    const struct hp1020_udc_in_observation *o,struct hp1020_udc_in_completion_facts f) {
    enum hp1020_udc_in_result r=enter(s);if(r)return r;
    if(!o)return leave(s,HP1020_UDC_IN_INVALID);
    if(!current(s,o->cookie))return leave(s,HP1020_UDC_IN_STALE);
    if(f.descriptor_visible>1 || f.memory_settled>1 || f.actual_known>1)
        return leave(s,HP1020_UDC_IN_INVALID);
    if(o->endpoint_fault && !s->fault_reason)s->fault_reason=o->endpoint_fault;
    if(s->fault_reason)return leave(s,fault(s));
    if(s->phase!=HP1020_UDC_IN_EXPOSED)return leave(s,HP1020_UDC_IN_INVALID);
    if(!f.descriptor_visible)return leave(s,HP1020_UDC_IN_WAIT);
    uint32_t status=be32(o->descriptor);
    if((status>>30)!=2)return leave(s,HP1020_UDC_IN_WAIT);
    if(be32(o->descriptor+4) || be32(o->descriptor+8)!=s->packet.dma || be32(o->descriptor+12) ||
        (status&UINT32_C(0x30000000)) || !(status&UINT32_C(0x08000000))) {
        s->fault_reason=UINT32_C(0x80000301);return leave(s,fault(s));
    }
    if(!f.memory_settled || !f.actual_known)return leave(s,HP1020_UDC_IN_WAIT);
    if(f.actual!=s->length) { s->fault_reason=UINT32_C(0x80000302);return leave(s,fault(s)); }
    s->last_adapter_result=hp1020_tusb_adapter_complete(s->adapter,s->cookie,XFER_RESULT_SUCCESS,s->length);
    if(s->last_adapter_result==HP1020_TUSB_WAIT)return leave(s,HP1020_UDC_IN_WAIT);
    if(s->last_adapter_result!=HP1020_TUSB_OK)return leave(s,HP1020_UDC_IN_ADAPTER_ERROR);
    retire(s);return leave(s,HP1020_UDC_IN_OK);
}
enum hp1020_udc_in_result hp1020_udc_in_request_cancel(struct hp1020_udc_in *s,
    struct hp1020_tusb_cookie c) {
    enum hp1020_udc_in_result r=enter(s);if(r)return r;
    if(!current(s,c))return leave(s,HP1020_UDC_IN_STALE);
    s->cancel_requested=1;return leave(s,HP1020_UDC_IN_OK);
}
enum hp1020_udc_in_result hp1020_udc_in_cancelled(struct hp1020_udc_in *s,
    struct hp1020_tusb_cookie c,uint8_t settled) {
    enum hp1020_udc_in_result r=enter(s);if(r)return r;
    if(!current(s,c))return leave(s,HP1020_UDC_IN_STALE);
    if(settled>1 || !s->cancel_requested)return leave(s,HP1020_UDC_IN_INVALID);
    if(!settled)return leave(s,HP1020_UDC_IN_WAIT);
    s->last_adapter_result=hp1020_tusb_adapter_cancelled(s->adapter,s->cookie);
    if(s->last_adapter_result==HP1020_TUSB_WAIT)return leave(s,HP1020_UDC_IN_WAIT);
    if(s->last_adapter_result!=HP1020_TUSB_OK)return leave(s,HP1020_UDC_IN_ADAPTER_ERROR);
    retire(s);return leave(s,HP1020_UDC_IN_OK);
}
