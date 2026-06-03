/* Function: 10013620 hp1020_send_or_raise_engine_msg_candidate */


void hp1020_send_or_raise_engine_msg_candidate(undefined4 param_1,undefined4 param_2)

{
  int iVar1;
  
  iVar1 = FUN_10013668(param_1,param_2,0);
  if (iVar1 != 0) {
    FUN_10006f00(DAT_10005f60,PTR_s_tx_queue_send___failed__MSG_LOST_100066f4,0,0);
  }
  return;
}


