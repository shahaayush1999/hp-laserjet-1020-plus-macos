/* Function: 1000f814 hp1020_print_mgr_return_work_to_jobmgr_candidate */


/* medium confidence: PrintMgr 0x11 continuation helper; pops active work and sends onward to JobMgr
   queue */

void hp1020_print_mgr_return_work_to_jobmgr_candidate(undefined4 param_1)

{
  undefined4 *puVar1;

  if (*(int *)(hp1020_print_mgr_state_ptr_word + 4) == 0) {
    hp1020_print_mgr_state_ptr_word[2] = hp1020_print_mgr_state_ptr_word[2] + '\x01';
  }
  puVar1 = (undefined4 *)hp1020_list_pop_head_candidate(PTR_DAT_10006328);
  puVar1[3] = 0;
  *puVar1 = 0;
  hp1020_runtime_service_2_candidate();
  hp1020_queue_send_candidate(3,param_1);
  return;
}
