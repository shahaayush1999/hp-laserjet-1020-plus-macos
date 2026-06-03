/* Function: 1000a2a4 FUN_1000a2a4 */


/* WARNING: Control flow encountered bad instruction data */

int FUN_1000a2a4(uint param_1)

{
  undefined4 *puVar1;
  int iVar2;
  int iVar3;
  
  puVar1 = (undefined4 *)FUN_100111b4(0x1f);
  iVar3 = DAT_10006018;
  if (((param_1 & 0xffff & DAT_10005f74) != 0x100) &&
     (((param_1 & DAT_10005e74) == 0 || ((param_1 & DAT_10005e34) != 0)))) {
    if ((param_1 & 0xffff) != DAT_10005f70) {
                    /* WARNING: Bad instruction - Truncating control flow here */
      halt_baddata();
    }
    iVar2 = FUN_1000a280(*puVar1);
    iVar3 = iVar2 + DAT_1000601c;
    if (puVar1[2] != 0) {
      iVar3 = (puVar1[2] + 1) * 100 + iVar2 + DAT_1000601c;
    }
  }
  FUN_100111d8(0x1f);
  return iVar3;
}


