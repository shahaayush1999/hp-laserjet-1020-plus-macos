/*
Function: 1000ad44 hp1020_acl_download_1000ad44
Strings:
- descriptor:agiACLDownload
*/


void hp1020_acl_download_1000ad44(undefined4 param_1)

{
  uint *puVar1;
  undefined4 *puVar2;
  
  puVar1 = DAT_10005e24;
  memw();
  memw();
  *DAT_10005e70 = *DAT_10005e70 | 0x80;
  memw();
  puVar2 = *(undefined4 **)PTR_DAT_10006068;
  memw();
  *puVar1 = *puVar1 | 0x80;
  (*(code *)*puVar2)(0,param_1);
  return;
}


