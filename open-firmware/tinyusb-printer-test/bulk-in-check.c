/* SPDX-License-Identifier: GPL-2.0-or-later
 * Real TinyUSB calls with the existing synthetic DCD. No controller access.
 */
#include "fixture.c"

#define CHECK(x) do { if (!(x)) return __LINE__; } while (0)
#define TRY(x) do { uint32_t failure=(x); if (failure) return failure; } while (0)
static uint8_t reply[65];
static const uint8_t expected[] =
    "@PJL ECHO HP1020_STATUS_PROBE\r\n\f0123456789abcdefFEDCBA9876543210";

static uint32_t service(void) {
    CHECK(hp1020_bulk_fixture_step(1,0,0,0,0)==HP1020_TUSB_OK);
    return 0;
}
static uint32_t setup(const uint8_t raw[8]) {
    memcpy(hp1020_bulk_fixture_input,raw,8);
    CHECK(hp1020_bulk_fixture_step(0,8,0,0,0)==HP1020_TUSB_OK);
    TRY(service());return 0;
}
static uint32_t settle(struct hp1020_tusb_cookie cookie,uint32_t result,uint32_t length) {
    CHECK(hp1020_bulk_fixture_step(2,cookie.id,result,length,0)==HP1020_TUSB_OK);
    TRY(service());return 0;
}
static uint32_t recover(void) {
    CHECK(hp1020_bulk_fixture_step(10,0,0,0,0)==HP1020_PRINTER_OK);
    CHECK(hp1020_bulk_fixture_step(11,0,1,0,0)==HP1020_PRINTER_OK);
    CHECK(hp1020_bulk_fixture_step(11,0,2,0,0)==HP1020_PRINTER_OK);
    CHECK(hp1020_bulk_fixture_step(15,0,0,0,0)==HP1020_TUSB_OK);
    CHECK(hp1020_bulk_fixture_step(11,0,4,0,0)==HP1020_PRINTER_OK);
    CHECK(hp1020_bulk_fixture_step(12,0,0,0,0)==HP1020_PRINTER_OK);
    if(packets[1].live)TRY(settle(packets[1].cookie,XFER_RESULT_SUCCESS,0));
    return 0;
}
static uint32_t start(uint32_t fill) {
    static const uint8_t configure[8]={0,9,1,0,0,0,0,0};
    CHECK(hp1020_bulk_fixture_reset(fill,64,0,UINT32_MAX)==HP1020_TUSB_OK);
    memcpy(reply,expected,64);reply[64]=0xa7;
    CHECK(hp1020_bulk_fixture_step(5,TUSB_SPEED_FULL,0,0,0)==HP1020_TUSB_OK);
    TRY(service());TRY(setup(configure));
    CHECK(packets[1].live && !packets[1].length);
    TRY(settle(packets[1].cookie,XFER_RESULT_SUCCESS,0));
    TRY(recover());return 0;
}
static uint32_t send(uint16_t length,struct hp1020_tusb_cookie *cookie) {
    uint32_t at=state.wire_bytes;
    CHECK(hp1020_tusb_adapter_send_in(&adapter,length?reply:NULL,length,cookie)==HP1020_TUSB_OK);
    CHECK(cookie->id && cookie->endpoint==0x81 && !cookie->sequence);
    CHECK(cookie->epoch==adapter.transport_epoch && cookie->generation==document.receive.generation);
    CHECK(packets[3].live && packets[3].buffer==(length?reply:NULL) && packets[3].length==length);
    CHECK(usbd_edpt_busy(0,0x81));
    CHECK(state.wire_bytes==at+length && !memcmp(hp1020_bulk_fixture_wire+at,expected,length));
    return 0;
}
static uint32_t take(struct hp1020_tusb_cookie cookie,uint8_t result,uint32_t length,uint8_t current) {
    struct hp1020_tusb_in_result event;
    CHECK(hp1020_tusb_adapter_take_in_result(&adapter,&event)==HP1020_TUSB_OK);
    CHECK(same_cookie(cookie,event.cookie) && event.result==result && event.actual==length && event.current==current);
    CHECK(!usbd_edpt_busy(0,0x81));return 0;
}

uint32_t hp1020_bulk_in_check(uint32_t scenario,uint32_t fill) {
    static const uint8_t soft_reset[8]={0x21,2,0,0,0,0,0,0};
    static const uint8_t get_config[8]={0x80,8,0,0,0,0,1,0};
    struct hp1020_tusb_cookie cookie={0},other={0};
    struct hp1020_tusb_in_result event;
    TRY(start(fill));
    if(scenario==0) {
        CHECK(hp1020_tusb_adapter_send_in(&adapter,NULL,1,&cookie)==HP1020_TUSB_INVALID && !cookie.id);
        CHECK(hp1020_tusb_adapter_send_in(&adapter,reply,0,&cookie)==HP1020_TUSB_INVALID && !cookie.id);
        CHECK(hp1020_tusb_adapter_send_in(&adapter,reply,65,&cookie)==HP1020_TUSB_INVALID && !cookie.id);
        const uint16_t lengths[3]={1,64,0};
        for(uint32_t i=0;i<3;i++) {
            TRY(send(lengths[i],&cookie));
            CHECK(!hp1020_tusb_adapter_driver()->deinit());
            CHECK(hp1020_tusb_adapter_take_in_result(&adapter,&event)==HP1020_TUSB_WAIT);
            CHECK(hp1020_tusb_adapter_send_in(&adapter,reply,1,&other)==HP1020_TUSB_WAIT && !other.id);
            TRY(settle(cookie,XFER_RESULT_SUCCESS,lengths[i]));
            CHECK(!hp1020_tusb_adapter_driver()->deinit());
            CHECK(hp1020_tusb_adapter_send_in(&adapter,reply,1,&other)==HP1020_TUSB_WAIT && !other.id);
            TRY(take(cookie,XFER_RESULT_SUCCESS,lengths[i],1));
        }
    } else if(scenario==1) {
        CHECK(hp1020_tusb_adapter_arm_out(&adapter)==HP1020_TUSB_OK);
        struct hp1020_tusb_cookie out=packets[2].cookie;
        TRY(send(32,&cookie));TRY(setup(get_config));
        CHECK(!packets[2].cancel_requested && !packets[3].cancel_requested);
        TRY(settle(packets[1].cookie,XFER_RESULT_SUCCESS,1));
        TRY(settle(packets[0].cookie,XFER_RESULT_SUCCESS,0));
        TRY(settle(out,XFER_RESULT_SUCCESS,0));
        CHECK(hp1020_tusb_adapter_pump(&adapter)==HP1020_RX_OK);
        CHECK(hp1020_tusb_adapter_arm_out(&adapter)==HP1020_TUSB_OK);
        TRY(settle(cookie,XFER_RESULT_SUCCESS,32));TRY(take(cookie,XFER_RESULT_SUCCESS,32,1));
        CHECK(packets[2].live && !packets[2].cancel_requested);
    } else if(scenario==2 || scenario==3) {
        state.fail_submission=scenario-1;
        CHECK(hp1020_tusb_adapter_send_in(&adapter,reply,32,&cookie)==HP1020_TUSB_ERROR);
        if(scenario==2) {
            CHECK(!cookie.id && !packets[3].live && !usbd_edpt_busy(0,0x81) && !adapter.fenced);
            TRY(send(32,&cookie));TRY(settle(cookie,XFER_RESULT_SUCCESS,32));
            TRY(take(cookie,XFER_RESULT_SUCCESS,32,1));
        } else {
            CHECK(cookie.id && packets[3].live && packets[3].cancel_requested);
            TRY(settle(cookie,XFER_RESULT_SUCCESS,32));TRY(take(cookie,XFER_RESULT_SUCCESS,32,0));
        }
    } else if(scenario==4) {
        CHECK(hp1020_tusb_adapter_arm_out(&adapter)==HP1020_TUSB_OK);
        TRY(send(32,&cookie));TRY(setup(soft_reset));
        CHECK(packets[2].cancel_requested && packets[3].cancel_requested);
        CHECK(hp1020_bulk_fixture_step(10,0,0,0,0)==HP1020_PRINTER_OK);
        CHECK(hp1020_bulk_fixture_step(11,0,1,0,0)==HP1020_PRINTER_WAIT);
        CHECK(hp1020_bulk_fixture_step(4,packets[2].cookie.id,0,0,0)==HP1020_TUSB_OK);
        TRY(service());
        CHECK(hp1020_bulk_fixture_step(11,0,1,0,0)==HP1020_PRINTER_OK);
        CHECK(hp1020_bulk_fixture_step(11,0,2,0,0)==HP1020_PRINTER_OK);
        CHECK(hp1020_bulk_fixture_step(11,0,4,0,0)==HP1020_PRINTER_WAIT);
        uint32_t epoch=adapter.transport_epoch,parts=printer.reset_parts;
        CHECK(hp1020_tusb_adapter_complete(&adapter,cookie,XFER_RESULT_SUCCESS,31)==HP1020_TUSB_INVALID);
        CHECK(hp1020_tusb_adapter_packet_fault(&adapter,cookie,1)==HP1020_TUSB_STALE);
        CHECK(adapter.transport_epoch==epoch && printer.reset_parts==parts);
        TRY(settle(cookie,XFER_RESULT_SUCCESS,32));TRY(recover());
        TRY(take(cookie,XFER_RESULT_SUCCESS,32,0));
        TRY(send(1,&other));
        CHECK(hp1020_tusb_adapter_complete(&adapter,cookie,XFER_RESULT_SUCCESS,32)==HP1020_TUSB_STALE);
        CHECK(same_cookie(packets[3].cookie,other) && packets[3].live);
        TRY(settle(other,XFER_RESULT_SUCCESS,1));TRY(take(other,XFER_RESULT_SUCCESS,1,1));
    } else if(scenario==5) {
        TRY(send(32,&cookie));TRY(settle(cookie,XFER_RESULT_SUCCESS,32));
        TRY(setup(soft_reset));TRY(recover());
        CHECK(hp1020_tusb_adapter_send_in(&adapter,reply,1,&other)==HP1020_TUSB_WAIT && !other.id);
        TRY(take(cookie,XFER_RESULT_SUCCESS,32,0));
        TRY(send(1,&other));TRY(settle(other,XFER_RESULT_SUCCESS,1));TRY(take(other,XFER_RESULT_SUCCESS,1,1));
    } else if(scenario>=6 && scenario<=8) {
        TRY(send(32,&cookie));
        uint32_t result=scenario==8?XFER_RESULT_INVALID:XFER_RESULT_SUCCESS;
        uint32_t length=scenario==6?31:scenario==7?33:32;
        CHECK(hp1020_bulk_fixture_step(2,cookie.id,result,length,0)==HP1020_TUSB_INVALID);
        CHECK(packets[3].live && packets[3].cancel_requested);
        CHECK(hp1020_tusb_adapter_take_in_result(&adapter,&event)==HP1020_TUSB_WAIT);
        CHECK(hp1020_bulk_fixture_step(4,cookie.id,0,0,0)==HP1020_TUSB_OK);
        TRY(service());TRY(take(cookie,XFER_RESULT_ABORTED,0,0));
    } else if(scenario==9) {
        TRY(send(32,&cookie));TRY(settle(cookie,XFER_RESULT_FAILED,7));
        TRY(take(cookie,XFER_RESULT_FAILED,7,0));
        TRY(setup(soft_reset));TRY(recover());
        TRY(send(32,&other));TRY(settle(other,XFER_RESULT_SUCCESS,32));TRY(take(other,XFER_RESULT_SUCCESS,32,1));
    } else if(scenario==10) {
        /* Independent minimal ZjStream: START_DOC followed by END_DOC. */
        static const uint8_t empty[36]={
            'J','Z','J','Z',0,0,0,16,0,0,0,0,0,0,0,0,0,0,0x5a,0x5a,
            0,0,0,16,0,0,0,1,0,0,0,0,0,0,0x5a,0x5a};
        CHECK(hp1020_tusb_adapter_arm_out(&adapter)==HP1020_TUSB_OK);
        memcpy(hp1020_bulk_fixture_input,empty,sizeof(empty));
        CHECK(hp1020_bulk_fixture_step(3,packets[2].cookie.id,sizeof(empty),0,0)==HP1020_TUSB_OK);
        TRY(settle(packets[2].cookie,XFER_RESULT_SUCCESS,sizeof(empty)));
        CHECK(hp1020_tusb_adapter_pump(&adapter)==HP1020_RX_OK);
        TRY(send(32,&cookie));
        CHECK(hp1020_tusb_adapter_close_input(&adapter)==HP1020_TUSB_OK);
        CHECK(hp1020_tusb_adapter_finish(&adapter)==HP1020_RX_OK);
        CHECK(document.finished && state.documents_completed==1);
        TRY(settle(cookie,XFER_RESULT_SUCCESS,32));TRY(take(cookie,XFER_RESULT_SUCCESS,32,1));
        TRY(send(1,&other));TRY(settle(other,XFER_RESULT_SUCCESS,1));TRY(take(other,XFER_RESULT_SUCCESS,1,1));
    } else if(scenario==11) {
        TRY(send(32,&cookie));adapter.transport_epoch=UINT32_MAX; /* Test-only saturation. */
        CHECK(hp1020_tusb_adapter_bus_reset(&adapter,TUSB_SPEED_FULL)==HP1020_TUSB_LIMIT);
        CHECK(packets[3].live && packets[3].cancel_requested);
        CHECK(hp1020_bulk_fixture_step(4,cookie.id,0,0,0)==HP1020_TUSB_OK);
        CHECK(hp1020_tusb_adapter_service(&adapter)==HP1020_TUSB_LIMIT);
        TRY(take(cookie,XFER_RESULT_ABORTED,0,0));
    } else return __LINE__;
    check_owned();
    CHECK(!state.violations && !memcmp(reply,expected,64) && reply[64]==0xa7);
    return 0;
}
