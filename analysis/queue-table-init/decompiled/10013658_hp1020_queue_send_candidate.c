/* Function: 10013658 hp1020_queue_send_candidate */


undefined4 hp1020_queue_send_candidate(undefined4 param_1,undefined4 param_2)

{
  undefined4 uVar1;
  
  uVar1 = hp1020_queue_send_indexed_candidate(param_1,param_2,0xffffffff);
  return uVar1;
}


