/* Function: 1000cd44 hp1020_pjl_response_send_candidate */


void hp1020_pjl_response_send_candidate(undefined4 param_1)

{
  undefined *puVar1;
  undefined4 uVar2;
  int iVar3;
  
  puVar1 = PTR_DAT_100060bc;
  iVar3 = *(int *)PTR_DAT_100060bc;
  uVar2 = hp1020_strlen_like(param_1);
  (**(code **)(iVar3 + 0x10))(*(undefined4 *)puVar1,param_1,uVar2);
  return;
}


