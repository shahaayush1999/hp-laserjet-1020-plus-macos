/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_USB_SERVICE_H
#define HP1020_USB_SERVICE_H
#include "../udc-publish/hp1020_udc_publish.h"
#include "../udc-in-publish/hp1020_udc_in_publish.h"
#include "../pjl-command/hp1020_pjl_command.h"

/* One shared controller/program/OUT/IN/command graph. Stationary objects,
 * serialized calls and hooks; no allocation, reinitialization or physical
 * backend. The platform still owns capture, exact-cookie settlement, actual
 * reset ingress and independently justified physical facts. */
struct hp1020_usb_service {
    struct hp1020_udc_publish *out;
    struct hp1020_udc_in_publish *in;
    struct hp1020_pjl_command *commands;
    uint8_t initialized;
};
bool hp1020_usb_service_init(struct hp1020_usb_service *,
    struct hp1020_udc_publish *,struct hp1020_udc_in_publish *,struct hp1020_pjl_command *);

/* Use these combined gates in place of the OUT-only gates. ALL three bits are
 * required before close_input/finish/finish_reset and manual EP0 publication.
 * A failure in either direction blocks ordinary service and new work; only
 * already admitted, inactive actual bus reset drainage retains SERVICE. A
 * terminal command ownership violation is also a fence, never restartable by
 * clearing an unrelated publisher failure. */
uint32_t hp1020_usb_service_progress(const struct hp1020_usb_service *);
/* Before complete_selection/grant, then obey that operation's own checks.
 * Does not require full progress: complete_selection may establish readiness. */
bool hp1020_usb_service_program_allowed(const struct hp1020_usb_service *);
/* Call in EVERY actual DCD submission, including EP0/offloaded status. Allows
 * the legitimate callback inside the command pump; never a new owner by itself. */
bool hp1020_usb_service_submission_allowed(struct hp1020_usb_service *);
/* Include in IN publisher io.ready. That hook runs with in->busy set, so this
 * predicate deliberately permits that one context. It is not ordinary progress
 * permission and does not supply physical readiness or a register lease. */
bool hp1020_usb_service_in_ready(const struct hp1020_usb_service *,struct hp1020_tusb_cookie);

enum hp1020_udc_publish_result hp1020_usb_service_control(struct hp1020_usb_service *);
/* Reaps a returned original reply even while failed. Pumps new input/status
 * only with current PUMP permission. WAIT does not mean physical inactivity. */
enum hp1020_rx_result hp1020_usb_service_pump(struct hp1020_usb_service *);
enum hp1020_udc_publish_result hp1020_usb_service_arm_out(struct hp1020_usb_service *,
    struct hp1020_udc_publish_facts);
enum hp1020_udc_in_publish_result hp1020_usb_service_publish_in(struct hp1020_usb_service *,
    struct hp1020_tusb_cookie,struct hp1020_udc_in_publish_facts_ext);
#endif
