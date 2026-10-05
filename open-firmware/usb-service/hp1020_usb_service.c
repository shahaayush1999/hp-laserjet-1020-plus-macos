/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "hp1020_usb_service.h"

#define SERVICE_ALL (HP1020_UDC_SETUP_ALLOW_SERVICE | HP1020_UDC_SETUP_ALLOW_ARM | HP1020_UDC_SETUP_ALLOW_PUMP)
static bool service_valid(const struct hp1020_usb_service *s) {
    return s && s->initialized && s->out && s->out->initialized &&
        s->out->out && s->out->out->initialized && s->out->program &&
        s->out->program->initialized && s->out->program->ingress &&
        s->out->program->ingress->initialized && s->in && s->in->initialized &&
        s->in->port && s->in->port->initialized && s->commands && s->commands->initialized &&
        s->commands->adapter && s->commands->adapter->initialized &&
        s->commands->adapter==s->out->out->adapter &&
        s->commands->adapter==s->out->program->ingress->adapter &&
        s->commands->adapter==s->in->port->adapter;
}
bool hp1020_usb_service_init(struct hp1020_usb_service *s,struct hp1020_udc_publish *out,
    struct hp1020_udc_in_publish *in,struct hp1020_pjl_command *commands) {
    if(!s || s->initialized)return false;
    const struct hp1020_usb_service candidate={out,in,commands,1};
    if(!service_valid(&candidate) || commands->busy || commands->adapter->busy ||
        commands->adapter->stack_active || in->busy || out->busy || out->arming ||
        out->servicing || out->program->busy || out->program->servicing)return false;
    *s=candidate;return true;
}
static uint32_t service_permission(const struct hp1020_usb_service *s) {
    const uint32_t permission=hp1020_udc_publish_progress(s->out);
    if(!s->in->failed && !s->commands->terminal)return permission;
    return hp1020_udc_setup_progress(s->out->program->ingress)==HP1020_UDC_SETUP_ALLOW_SERVICE ?
        permission&HP1020_UDC_SETUP_ALLOW_SERVICE:0;
}
static bool service_ingress_current(const struct hp1020_usb_service *s) {
    const struct hp1020_udc_setup *ingress=s->out->program->ingress;
    const struct hp1020_tusb_adapter *a=s->commands->adapter;
    /* A real DCD callback runs inside adapter busy/stack_active, so the ordinary
     * progress predicate cannot be used here. Preserve the bridge's capture,
     * epoch and actual-reset barriers without rejecting that valid callback. */
    return !ingress->busy && !ingress->terminal && !a->exhausted &&
        ingress->pending_kind==HP1020_UDC_SETUP_PENDING_NONE &&
        a->control_epoch==ingress->adapter_control_epoch &&
        (!ingress->reset_control_epoch || ingress->reset_control_epoch!=a->control_epoch ||
         a->active_control_epoch==ingress->reset_control_epoch);
}
uint32_t hp1020_usb_service_progress(const struct hp1020_usb_service *s) {
    if(!service_valid(s) || s->in->busy || s->commands->busy)return 0;
    return service_permission(s);
}
bool hp1020_usb_service_program_allowed(const struct hp1020_usb_service *s) {
    return service_valid(s) && !s->in->failed && !s->in->busy && !s->commands->busy &&
        !s->commands->terminal &&
        !s->out->failed && !s->out->busy && !s->out->arming && !s->out->servicing;
}
bool hp1020_usb_service_submission_allowed(struct hp1020_usb_service *s) {
    return service_valid(s) && !s->in->failed && !s->in->busy && !s->commands->terminal &&
        service_ingress_current(s) &&
        hp1020_udc_publish_submission_allowed(s->out);
}
bool hp1020_usb_service_in_ready(const struct hp1020_usb_service *s,struct hp1020_tusb_cookie c) {
    if(!service_valid(s) || s->in->failed || s->commands->busy || s->commands->terminal ||
        service_permission(s)!=SERVICE_ALL)return false;
    const struct hp1020_tusb_cookie original=s->in->port->cookie;
    return c.id && c.id==original.id && c.epoch==original.epoch &&
        c.generation==original.generation && c.sequence==original.sequence && c.endpoint==original.endpoint;
}
enum hp1020_udc_publish_result hp1020_usb_service_control(struct hp1020_usb_service *s) {
    if(!service_valid(s))return HP1020_UDC_PUBLISH_INVALID;
    if(!(hp1020_usb_service_progress(s)&HP1020_UDC_SETUP_ALLOW_SERVICE))return HP1020_UDC_PUBLISH_WAIT;
    return hp1020_udc_publish_service(s->out);
}
enum hp1020_rx_result hp1020_usb_service_pump(struct hp1020_usb_service *s) {
    if(!service_valid(s))return HP1020_RX_ORDER;
    if(s->in->busy || s->out->busy || s->out->arming || s->out->servicing ||
        s->out->program->busy || s->out->program->servicing)return HP1020_RX_WAIT;
    /* Collection may be necessary to clear a failure that itself prohibits
     * PUMP. It cannot consume input or acquire a new IN owner. */
    enum hp1020_rx_result r=hp1020_pjl_command_reap(s->commands);
    if(r)return r;
    if(!(hp1020_usb_service_progress(s)&HP1020_UDC_SETUP_ALLOW_PUMP))return HP1020_RX_WAIT;
    return hp1020_pjl_command_pump(s->commands);
}
enum hp1020_udc_publish_result hp1020_usb_service_arm_out(struct hp1020_usb_service *s,
    struct hp1020_udc_publish_facts facts) {
    if(!service_valid(s))return HP1020_UDC_PUBLISH_INVALID;
    if(hp1020_usb_service_progress(s)!=SERVICE_ALL)return HP1020_UDC_PUBLISH_WAIT;
    return hp1020_udc_publish_arm_out(s->out,facts);
}
enum hp1020_udc_in_publish_result hp1020_usb_service_publish_in(struct hp1020_usb_service *s,
    struct hp1020_tusb_cookie c,struct hp1020_udc_in_publish_facts_ext facts) {
    if(!service_valid(s))return HP1020_IN_PUBLISH_INVALID;
    if(hp1020_usb_service_progress(s)!=SERVICE_ALL)return HP1020_IN_PUBLISH_WAIT;
    return hp1020_udc_in_publish_packet(s->in,c,facts);
}
