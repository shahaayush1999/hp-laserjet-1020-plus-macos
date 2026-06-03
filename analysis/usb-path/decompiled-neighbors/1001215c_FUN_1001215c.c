/*
Function: 1001215c FUN_1001215c
Score: 5
*/


void FUN_1001215c(int param_1)

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


