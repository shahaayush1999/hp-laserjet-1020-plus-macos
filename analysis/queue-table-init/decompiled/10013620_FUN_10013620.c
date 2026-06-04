/* Function: 10013620 FUN_10013620 */


void FUN_10013620(undefined4 param_1,undefined4 param_2)

{
  int iVar1;
  
  iVar1 = hp1020_queue_send_indexed_candidate(param_1,param_2,0);
  if (iVar1 != 0) {
    FUN_10006f00(DAT_10005f60,PTR_s_tx_queue_send___failed__MSG_LOST_100066f4,0,0);
  }
  return;
}


