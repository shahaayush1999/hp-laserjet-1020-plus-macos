/* Function: 1001215c hp1020_queue_receive_wrapper_candidate */


void hp1020_queue_receive_wrapper_candidate(int param_1)

{
  undefined4 uVar1;
  undefined1 auStack_30 [48];
  
  uVar1 = 1;
  if ((param_1 != 1) && (uVar1 = 4, param_1 == 2)) {
    uVar1 = 2;
  }
  threadx_queue_receive_candidate(PTR_DAT_10006530,uVar1,0,auStack_30,0xffffffff);
  return;
}


