/* Function: 100163b0 hp1020_engine_thread_candidate */


/* high confidence: Engine queue consumer */

void hp1020_engine_thread_candidate(void)

{
  uint uVar1;
  undefined *puVar2;
  uint uVar3;
  int iVar4;
  undefined4 uStack_30;
  undefined4 uStack_2c;
  
  puVar2 = PTR_DAT_10006920;
  *(undefined4 *)(PTR_DAT_10006920 + 0x68) = 0;
  FUN_1001215c(2);
  hp1020_engine_preflight_candidate();
  uVar1 = DAT_10006420;
  *(undefined4 *)(puVar2 + 0x44) = DAT_10005e34;
  while (uVar3 = hp1020_engine_status_poll_candidate(0), (uVar3 & uVar1) == uVar1) {
    threadx_sleep_candidate(1);
  }
  hp1020_engine_init_step_candidate();
  hp1020_engine_register_handlers_candidate();
  hp1020_register_event_handler_candidate
            (0xf,PTR_hp1020_engine_event_0x0f_config_callback_candidate_100069b4);
  puVar2 = PTR_LAB_100069b8;
  hp1020_register_event_handler_candidate(0x10,PTR_LAB_100069b8);
  hp1020_register_event_handler_candidate(0x11,puVar2);
  hp1020_register_event_handler_candidate(0x12,puVar2);
  hp1020_register_event_handler_candidate(0x13,puVar2);
  hp1020_register_event_handler_candidate(0x14,puVar2);
  hp1020_engine_init_step_candidate();
  uStack_2c = 2;
  uStack_30 = 0x16;
  hp1020_queue_send_candidate(1,&uStack_30);
  FUN_10012184(2);
  puVar2 = PTR_DAT_10006920;
  iVar4 = *(int *)(PTR_DAT_10006920 + 0x24);
  while (iVar4 == 0) {
    iVar4 = threadx_queue_receive_wait_candidate
                      (hp1020_eng_msg_queue_object_ptr_word,&uStack_30,0x32);
    if (iVar4 == 0) {
      hp1020_engine_message_dispatch_candidate(&uStack_30);
    }
    else {
      hp1020_engine_status_poll_candidate(0);
    }
    iVar4 = *(int *)(puVar2 + 0x24);
  }
  return;
}


