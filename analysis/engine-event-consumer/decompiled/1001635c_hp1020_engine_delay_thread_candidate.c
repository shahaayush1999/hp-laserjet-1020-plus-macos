/* Function: 1001635c hp1020_engine_delay_thread_candidate */


/* high confidence: Engine delay queue consumer */

void hp1020_engine_delay_thread_candidate(void)

{
  undefined *puVar1;
  int iVar2;
  int aiStack_30 [12];
  
  FUN_1001214c();
  puVar1 = PTR_DAT_10006920;
  iVar2 = *(int *)(PTR_DAT_10006920 + 0x24);
  while (iVar2 == 0) {
    iVar2 = threadx_queue_receive_wait_candidate(PTR_DAT_1000699c,aiStack_30,0xffffffff);
    if ((((iVar2 == 0) && (aiStack_30[0] == 0x11)) && (puVar1[0x28] != '\x01')) &&
       (threadx_sleep_candidate(0x9b), puVar1[0x28] != '\x01')) {
      hp1020_send_or_raise_engine_msg_candidate(1,aiStack_30);
    }
    iVar2 = *(int *)(puVar1 + 0x24);
  }
  return;
}


