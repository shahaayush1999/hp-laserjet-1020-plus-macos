/* Function: 1000f814 FUN_1000f814 */


void FUN_1000f814(undefined4 param_1)

{
  undefined4 *puVar1;
  
  if (*(int *)(PTR_DAT_10006338 + 4) == 0) {
    PTR_DAT_10006338[2] = PTR_DAT_10006338[2] + '\x01';
  }
  puVar1 = (undefined4 *)FUN_10013050(PTR_DAT_10006328);
  puVar1[3] = 0;
  *puVar1 = 0;
  FUN_10013408();
  hp1020_queue_send_candidate(3,param_1);
  return;
}


