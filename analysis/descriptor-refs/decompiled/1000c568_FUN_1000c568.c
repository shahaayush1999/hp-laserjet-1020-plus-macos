/* Function: 1000c568 FUN_1000c568 */


void FUN_1000c568(undefined4 param_1)

{
  undefined2 uVar1;
  undefined *puVar2;
  undefined *puVar3;
  undefined *puVar4;
  int iVar5;
  short sVar7;
  undefined4 uVar6;
  ushort uVar8;
  uint uVar9;
  
  puVar3 = PTR_PTR_1000624c;
  uVar8 = 0;
  uVar9 = 0;
  do {
    iVar5 = FUN_1001684c(param_1,*(undefined4 *)(puVar3 + uVar9 * 4));
    puVar4 = PTR_DAT_10006250;
    puVar2 = PTR_DAT_100060d4;
    if (iVar5 == 0) break;
    uVar8 = uVar8 + 1;
    uVar9 = (uint)uVar8;
  } while (uVar9 < 10);
  uVar1 = *(undefined2 *)(PTR_DAT_100060dc + 4);
  *(undefined4 *)PTR_DAT_100060d4 = *(undefined4 *)PTR_DAT_100060dc;
  *(undefined2 *)(puVar2 + 4) = uVar1;
  FUN_1001b544(puVar2,puVar4);
  FUN_1001b544(puVar2,PTR_DAT_100060e4);
  FUN_1001b544(puVar2,param_1);
  puVar3 = PTR_DAT_100060ec;
  FUN_1001b544(puVar2,PTR_DAT_100060ec);
  if (uVar8 == 10) {
    FUN_1001b544(puVar2,PTR_DAT_10006254);
    FUN_1001b544(puVar2,puVar3);
  }
  else {
    switch(uVar8) {
    case 0:
      uVar6 = FUN_100111b4(0x1e);
      puVar3 = PTR_DAT_100060d4;
      FUN_1001b544(PTR_DAT_100060d4,uVar6);
      FUN_1001b544(puVar3,PTR_DAT_100060ec);
      FUN_100111d8(0x1e);
      break;
    case 1:
      FUN_1000bd04(PTR_DAT_100060d4);
      break;
    case 2:
      FUN_1000ba48(PTR_DAT_100060d4);
      break;
    case 3:
      FUN_1000bfb0(PTR_DAT_100060d4);
      break;
    case 4:
      FUN_1000c230(PTR_DAT_100060d4);
      break;
    case 5:
      FUN_1000bfc8(PTR_DAT_100060d4);
      break;
    case 7:
      FUN_1000ba98(PTR_DAT_100060d4);
    }
  }
  puVar3 = PTR_DAT_100060d4;
  FUN_1001b544(PTR_DAT_100060d4,PTR_DAT_100060f8);
  sVar7 = FUN_100169d4(puVar3);
  uVar6 = FUN_1000dc00(sVar7 + 1);
  FUN_1001693c(uVar6,puVar3);
  FUN_1000cd44(uVar6,1);
  FUN_1000b1c4();
  return;
}


