/* SPDX-License-Identifier: GPL-2.0-or-later
 * Separate reset-profile compiler layout witness. Authored unexecuted, 2026-10-03.
 * Compare with the independently frozen target32 table before using offsets.
 * No functions, addresses, writable storage or expected result bytes.
 */
#include "hp1020_usb_runtime_contract.h"

#define OBJECT(id,type) (id),sizeof(type),_Alignof(type)
#define FIELD(id,object,type,member) (id),(object),offsetof(type,member),sizeof(((type *)0)->member)
#define DOC(id,member) FIELD(id,1,struct hp1020_usb_document,member)
#define MEM(id,member) FIELD(id,2,struct hp1020_usb_document_memory,member)
#define PRINTER(id,member) FIELD(id,3,struct hp1020_usb_printer,member)
#define ADAPTER(id,member) FIELD(id,4,struct hp1020_tusb_adapter,member)
#define OUT(id,member) FIELD(id,5,struct hp1020_udc_out,member)
#define EP0(id,member) FIELD(id,7,struct hp1020_udc_ep0,member)
#define SETUP(id,member) FIELD(id,9,struct hp1020_udc_setup,member)
#define PROGRAM(id,member) FIELD(id,10,struct hp1020_udc_program,member)
#define PUBLISH(id,member) FIELD(id,11,struct hp1020_udc_publish,member)
#define ACQUIRE(id,member) FIELD(id,12,struct hp1020_udc_acquire,member)
#define PROVIDER(id,member) FIELD(id,13,struct hp1020_usb_runtime_provider_type,member)
#define WITNESS(id,member) FIELD(id,15,struct hp1020_usb_runtime_witness_type,member)

const uint32_t hp1020_usb_runtime_layout[HP1020_USB_RUNTIME_LAYOUT_WORDS]
__attribute__((used,section(".rodata.hp1020_usb_runtime_layout"))) = {
    HP1020_USB_RUNTIME_LAYOUT_MAGIC,HP1020_USB_RUNTIME_VERSION,HP1020_USB_RUNTIME_LAYOUT_WORDS,
    HP1020_USB_RUNTIME_LAYOUT_OBJECTS,HP1020_USB_RUNTIME_LAYOUT_FIELDS,
    OBJECT(1,struct hp1020_usb_document),
    OBJECT(2,struct hp1020_usb_document_memory),
    OBJECT(3,struct hp1020_usb_printer),
    OBJECT(4,struct hp1020_tusb_adapter),
    OBJECT(5,struct hp1020_udc_out),
    OBJECT(6,struct hp1020_udc_out_memory),
    OBJECT(7,struct hp1020_udc_ep0),
    OBJECT(8,struct hp1020_udc_ep0_memory),
    OBJECT(9,struct hp1020_udc_setup),
    OBJECT(10,struct hp1020_udc_program),
    OBJECT(11,struct hp1020_udc_publish),
    OBJECT(12,struct hp1020_udc_acquire),
    OBJECT(13,struct hp1020_usb_runtime_provider_type),
    OBJECT(14,struct hp1020_usb_runtime_mailbox_type),
    OBJECT(15,struct hp1020_usb_runtime_witness_type),
    OBJECT(16,uint8_t[16]),
    DOC(1,receive.generation),DOC(2,receive.issued),DOC(3,receive.consumed),
    DOC(4,receive.count),DOC(5,receive.stopped),DOC(6,receive.quiescent),DOC(7,receive.error),
    DOC(8,finished),DOC(9,output.finished),DOC(10,output.error),DOC(11,output_quiescent),
    DOC(12,payload_error),DOC(13,feed_generation),DOC(14,output.stream.parser.documents),
    DOC(15,output.stream.pages),DOC(16,output.pages_drained),DOC(17,output.documents_completed),
    DOC(18,output.document_first_page),DOC(19,output.ring.copied_rows),
    DOC(20,output.ring.accepted_rows),DOC(21,output.ring.completed_rows),
    DOC(22,output.ring.error),DOC(23,output.ring.slots),
    MEM(24,receive.data),MEM(25,output.stream),MEM(26,output.slots),
    ADAPTER(27,control_epoch),ADAPTER(28,active_control_epoch),
    ADAPTER(29,transport_epoch),ADAPTER(30,active_transport_epoch),
    ADAPTER(31,last_submission_id),ADAPTER(32,opened),ADAPTER(33,configuration_value),
    ADAPTER(34,input_closed),ADAPTER(35,fenced),ADAPTER(36,prepared),ADAPTER(37,busy),
    ADAPTER(38,stack_active),ADAPTER(39,delivering_live),ADAPTER(40,response_owned),
    ADAPTER(41,owners[0].state),ADAPTER(42,owners[1].state),ADAPTER(43,owners[2].state),
    ADAPTER(44,owners[2].cookie.id),ADAPTER(45,owners[2].cookie.epoch),
    ADAPTER(46,owners[2].cookie.generation),ADAPTER(47,owners[2].cookie.sequence),
    ADAPTER(48,owners[2].cookie.endpoint),ADAPTER(49,owners[2].buffer),
    ADAPTER(50,owners[2].length),ADAPTER(51,owners[2].actual),
    PRINTER(52,reset_active),PRINTER(53,reset_parts),PRINTER(54,last_recovery_id),
    PRINTER(55,current_request_id),PRINTER(56,reset_request_id),
    ADAPTER(57,class_request_id),ADAPTER(58,reset_transport_epoch),
    OUT(59,phase),OUT(60,buffer.cpu),OUT(61,buffer.dma),OUT(62,descriptor.cpu),
    OUT(63,descriptor.dma),OUT(64,cookie.id),OUT(65,cookie.epoch),OUT(66,cookie.generation),
    OUT(67,cookie.sequence),OUT(68,cookie.endpoint),
    EP0(69,slots[0].phase),EP0(70,slots[1].phase),
    PROGRAM(71,failed),PROGRAM(72,completed_mask),PROGRAM(73,selection_mask),PROGRAM(74,binding_ready),
    PUBLISH(75,failed),PUBLISH(76,prefix),ACQUIRE(77,failure_valid),ACQUIRE(78,last.prefix),
    SETUP(79,last_sequence),SETUP(80,last_admitted_sequence),SETUP(81,pending_kind),
    PROVIDER(82,bulk.live),PROVIDER(83,closing),PROVIDER(84,finished),
    PROVIDER(85,bulk.original),PROVIDER(86,bulk.requested),PROVIDER(87,ep0.live),
    PROVIDER(88,recovery.recovery_id),PROVIDER(89,recovery.generation),PROVIDER(90,steps),
    WITNESS(91,io),WITNESS(92,ranges),WITNESS(93,binds),WITNESS(94,device),
    WITNESS(95,pixels),WITNESS(96,documents),
    97,16,0,sizeof(hp1020_usb_runtime_setup_memory),
    FIELD(98,14,struct hp1020_usb_runtime_mailbox_type,words),
    DOC(99,feeding),PROVIDER(100,callback_depth),SETUP(101,capture.record),
    PROVIDER(102,reset_cookie.id),PROVIDER(103,reset_cookie.epoch),
    PROVIDER(104,reset_cookie.generation),PROVIDER(105,reset_cookie.sequence),
    PROVIDER(106,reset_cookie.endpoint),PROVIDER(107,bulk.cancel_requested),
    OUT(108,cancel_requested),WITNESS(109,checks),ADAPTER(110,last_class_result),
    ADAPTER(111,owners[2].cancel_requested),ADAPTER(112,owners[2].expected_cancel),
    PRINTER(113,last_request_id),PRINTER(114,current_action),PRINTER(115,current_issued),
    PRINTER(116,ep0_live),PRINTER(117,ep0_request_id),ADAPTER(118,deferred)
};
_Static_assert(sizeof(hp1020_usb_runtime_layout)==4u*HP1020_USB_RUNTIME_LAYOUT_WORDS,"layout bytes");
