/* Function: 10010c98 FUN_10010c98 */


bool FUN_10010c98(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  undefined4 *puVar1;
  uint uVar2;
  undefined4 local_30;
  undefined4 uStack_2c;

  FUN_100181a4(PTR_DAT_10006430,0xffffffff);
  uVar2 = *(uint *)PTR_DAT_10006454;
  if (uVar2 < 10) {
    *(uint *)PTR_DAT_10006454 = uVar2 + 1;
    puVar1 = (undefined4 *)(PTR_DAT_1000645c + uVar2 * 0x14);
    *puVar1 = param_1;
    puVar1[1] = param_2;
    puVar1[2] = param_3;
    puVar1[3] = param_4;
    puVar1[4] = param_2;
    local_30 = 0x44;
    uStack_2c = 0;
    hp1020_queue_send_candidate(0xf,&local_30);
  }
  FUN_10018214(PTR_DAT_10006430);
  return uVar2 < 10;
}
