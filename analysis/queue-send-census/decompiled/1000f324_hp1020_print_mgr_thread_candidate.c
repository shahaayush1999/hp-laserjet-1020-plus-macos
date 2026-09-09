/* Function: 1000f324 hp1020_print_mgr_thread_candidate */


/* print-manager fallout mapping candidate */

void hp1020_print_mgr_thread_candidate(undefined4 param_1,undefined4 param_2)

{
  undefined *puVar1;
  int aiStack_50 [20];

  FUN_1001214c();
  hp1020_datastore_register_queue_subscriber_candidate(0x18,1);
  hp1020_datastore_register_queue_subscriber_candidate(1,1);
  aiStack_50[0] = 0x18;
  hp1020_queue_send_candidate(0,aiStack_50);
  puVar1 = hp1020_print_mgr_state_ptr_word;
  do {
    threadx_queue_receive_wait_candidate(PTR_DAT_1000632c,aiStack_50,0xffffffff);
  } while (0x38 < aiStack_50[0] - 0xbU);
                    /* WARNING: Could not recover jumptable at 0x1000f377. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(PTR_switchdataD_100048f0_10006360 + (aiStack_50[0] - 0xbU) * 4))
            (param_1,param_2,0,puVar1);
  return;
}
