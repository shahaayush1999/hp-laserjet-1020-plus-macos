/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef HP1020_SYNTHETIC_TUSB_CONFIG_H
#define HP1020_SYNTHETIC_TUSB_CONFIG_H

/* Synthetic RAM-only device controller. No portable MCU/DCD is compiled. */
#define CFG_TUSB_MCU OPT_MCU_NONE
#define CFG_TUSB_OS OPT_OS_NONE
#define CFG_TUSB_DEBUG 0
#define CFG_TUD_ENABLED 1
#define CFG_TUH_ENABLED 0
#define CFG_TUC_ENABLED 0
#define CFG_TUD_MAX_SPEED OPT_MODE_FULL_SPEED
#define CFG_TUD_ENDPOINT0_SIZE 64
#define CFG_TUD_ENDPOINT0_BUFSIZE 64
#define CFG_TUD_INTERFACE_MAX 4
#define TUP_DCD_ENDPOINT_MAX 8
#define CFG_TUD_ENDPPOINT_MAX 8
#define TUP_DCD_EDPT_CLOSE_API
#define CFG_TUD_MEM_DCACHE_ENABLE 0
#define CFG_TUD_TASK_QUEUE_SZ 16
#define CFG_TUD_TASK_EVENTS_PER_RUN 16

/* The application driver composes the existing class/document component. */
#define CFG_TUD_PRINTER 0
#define CFG_TUD_CDC 0
#define CFG_TUD_MSC 0
#define CFG_TUD_HID 0
#define CFG_TUD_MIDI 0
#define CFG_TUD_MIDI2 0
#define CFG_TUD_AUDIO 0
#define CFG_TUD_VIDEO 0
#define CFG_TUD_VENDOR 0
#define CFG_TUD_USBTMC 0
#define CFG_TUD_DFU_RUNTIME 0
#define CFG_TUD_DFU 0
#define CFG_TUD_ECM_RNDIS 0
#define CFG_TUD_NCM 0
#define CFG_TUD_BTH 0
#define CFG_TUD_MTP 0
#endif
