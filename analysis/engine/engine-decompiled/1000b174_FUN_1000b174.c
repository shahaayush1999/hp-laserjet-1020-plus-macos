/* Function: 1000b174 FUN_1000b174 */


undefined4 FUN_1000b174(int param_1)

{
  int iVar1;
  undefined4 local_40;
  int *piStack_3c;
  int aiStack_30 [12];
  
  local_40 = 0x1c;
  piStack_3c = aiStack_30;
  FUN_10010f54(&local_40);
  if (aiStack_30[0] != 0) {
    FUN_10013408();
    aiStack_30[0] = 0;
  }
  if (param_1 != 0) {
    iVar1 = FUN_100169d4(param_1);
    aiStack_30[0] = FUN_1000dc00(iVar1 + 1);
    FUN_1001693c(aiStack_30[0],param_1);
  }
  FUN_10010fd0(&local_40);
  return 1;
}


