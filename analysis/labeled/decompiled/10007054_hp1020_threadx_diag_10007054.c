/*
Function: 10007054 hp1020_threadx_diag_10007054
Strings:
- descriptor:dprintf mutex
*/


void hp1020_threadx_diag_10007054(undefined1 param_1)

{
  undefined *puVar1;
  undefined *puVar2;
  int iVar3;
  undefined1 *puVar4;
  
  puVar2 = PTR_DAT_10005d24;
  puVar1 = PTR_DAT_10005d20;
  puVar4 = *(undefined1 **)PTR_DAT_10005d20;
  *puVar4 = param_1;
  iVar3 = *(int *)puVar2;
  *(undefined1 **)puVar1 = puVar4 + 1;
  *(int *)puVar2 = iVar3 + 1;
  return;
}


