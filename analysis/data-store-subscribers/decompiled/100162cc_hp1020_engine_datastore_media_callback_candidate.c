/* Function: 100162cc hp1020_engine_datastore_media_callback_candidate */


/* data-store subscriber mapping candidate */

void hp1020_engine_datastore_media_callback_candidate(undefined4 param_1,undefined4 param_2)

{
  undefined4 uVar1;
  int iVar2;
  undefined4 uVar3;

  uVar1 = hp1020_datastore_get_value_candidate(param_1);
  switch(param_1) {
  case 0x10:
    uVar1 = 0x200;
    break;
  case 0x11:
    uVar1 = 0x201;
    break;
  case 0x12:
    uVar1 = 0x202;
    break;
  case 0x13:
    uVar1 = 0x203;
    break;
  case 0x14:
    uVar1 = 0x204;
  }
  iVar2 = hp1020_engine_lookup_media_record_candidate(param_2);
  uVar3 = *(undefined4 *)(iVar2 + 4);
  iVar2 = hp1020_engine_lookup_media_record_candidate(uVar1);
  *(undefined4 *)(iVar2 + 4) = uVar3;
  return;
}
