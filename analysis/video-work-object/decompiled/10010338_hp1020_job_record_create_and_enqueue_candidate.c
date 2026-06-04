/* Function: 10010338 hp1020_job_record_create_and_enqueue_candidate */


void hp1020_job_record_create_and_enqueue_candidate(undefined4 *param_1,int param_2)

{
  int iVar1;
  undefined4 local_30 [3];
  int iStack_24;

  iVar1 = hp1020_alloc_with_retry_candidate(0x78,1);
  hp1020_work_common_init_candidate();
  *(undefined4 *)(iVar1 + 0x70) = 0;
  *(undefined4 *)(iVar1 + 0x74) = 0;
  *(undefined4 *)(iVar1 + 0x48) = 0;
  *(undefined4 *)(iVar1 + 0x60) = 0;
  *(undefined2 *)(iVar1 + 0x6c) = 0;
  *(undefined4 *)(iVar1 + 0x5c) = param_1[1];
  *(undefined4 *)(iVar1 + 0x58) = *param_1;
  *(undefined4 *)(iVar1 + 0x60) = param_1[3];
  *(undefined4 *)(iVar1 + 100) = param_1[4];
  *(undefined4 *)(iVar1 + 0x48) = param_1[2];
  if (param_2 != 0) {
    hp1020_work_populate_from_page_params_candidate(iVar1,param_2);
  }
  local_30[0] = 1;
  iStack_24 = iVar1;
  hp1020_queue_send_candidate(3,local_30);
  return;
}
