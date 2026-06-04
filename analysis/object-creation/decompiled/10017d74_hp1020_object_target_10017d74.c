/* Function: 10017d74 hp1020_object_target_10017d74 */


undefined4
hp1020_object_target_10017d74
          (int *param_1,int param_2,int param_3,int param_4,int param_5,int param_6)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 != DAT_100065a8)) {
    return 6;
  }
  if (((param_2 != 0) && (((param_3 != 0 && (param_4 != 0)) && (param_5 != 0)))) && (param_6 != 0))
  {
    uVar1 = FUN_1001b8c8(param_1,param_2,param_3,param_4,param_5,param_6);
    return uVar1;
  }
  return 3;
}


