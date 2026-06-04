/* Function: 10017e9c hp1020_object_target_10017e9c */


undefined4
hp1020_object_target_10017e9c
          (int *param_1,int param_2,int param_3,int param_4,int param_5,int param_6,int param_7)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 != DAT_100065d0)) {
    return 0x1c;
  }
  if (((param_2 != 0) && (((param_3 != 0 && (param_4 != 0)) && (param_5 != 0)))) &&
     ((param_6 != 0 && (param_7 != 0)))) {
    uVar1 = FUN_1001b8ec(param_1,param_2,param_3,param_4,param_5,param_6,param_7);
    return uVar1;
  }
  return 3;
}


