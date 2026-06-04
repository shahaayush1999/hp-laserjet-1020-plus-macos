/* Function: 100181dc hp1020_object_target_100181dc */


undefined4
hp1020_object_target_100181dc
          (int *param_1,int param_2,int param_3,int param_4,int param_5,int param_6)

{
  undefined4 uVar1;
  
  if ((param_1 == (int *)0x0) || (*param_1 != DAT_100065bc)) {
    return 0xc;
  }
  if (((param_2 != 0) && (((param_3 != 0 && (param_4 != 0)) && (param_5 != 0)))) && (param_6 != 0))
  {
    uVar1 = FUN_1001ba2c(param_1,param_2,param_3,param_4,param_5,param_6);
    return uVar1;
  }
  return 3;
}


