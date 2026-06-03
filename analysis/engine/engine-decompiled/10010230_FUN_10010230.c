/* Function: 10010230 FUN_10010230 */


void FUN_10010230(int *param_1)

{
  undefined *puVar1;
  
  if (*param_1 == 0x17) {
    if (PTR_DAT_10006338[8] != '\0') {
      PTR_DAT_10006338[8] = PTR_DAT_10006338[8] + -1;
    }
  }
  else {
    if (*param_1 == 0xb) {
      if ((*PTR_DAT_10006338 == '\0') && (*(int *)(PTR_DAT_10006338 + 0x10) == DAT_100063a8)) {
        FUN_10010218(0,0x4a,0,0);
      }
    }
    puVar1 = PTR_DAT_10006338;
    if (((PTR_DAT_10006338[8] == '\0') && (*(int *)(PTR_DAT_10006338 + 0xc) == 0)) &&
       ((*PTR_DAT_10006338 == '\0' || (PTR_DAT_10006338[2] == '\0')))) {
      FUN_10010218(0,0x18,0,0);
      puVar1[8] = puVar1[8] + '\x01';
    }
  }
  return;
}


