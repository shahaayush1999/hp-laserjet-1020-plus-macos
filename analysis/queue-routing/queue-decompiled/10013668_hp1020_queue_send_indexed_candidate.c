/* Function: 10013668 hp1020_queue_send_indexed_candidate */


undefined4 hp1020_queue_send_indexed_candidate(int param_1,undefined4 param_2,undefined4 param_3)

{
  int iVar1;
  
  iVar1 = threadx_queue_send_wait_candidate
                    (*(undefined4 *)(param_1 * 4 + DAT_100066f0),param_2,param_3);
  if (iVar1 == 0) {
    return 0;
  }
  return 0xffffffff;
}


