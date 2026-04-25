# ============================================================
# cargar_contexto_pvz.ps1
# Carga el contexto completo de PVZFUSIONMOD en Cognia Dev
# Ejecutar con: .\cargar_contexto_pvz.ps1
# ============================================================

$base = "http://localhost:8001/api/memoria"

function Post($url, $body) {
    try {
        $json = $body | ConvertTo-Json -Depth 5
        Invoke-RestMethod -Uri $url -Method POST -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($json)) | Out-Null
        Write-Host "  OK" -ForegroundColor Green
    } catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
    }
}

Write-Host "`n== PVZFUSIONMOD -> Cognia Dev ==" -ForegroundColor Cyan
Write-Host "Cargando contexto del proyecto...`n"

# ── DATOS DEL PROYECTO ──────────────────────────────────────
Write-Host "[1/4] Datos del proyecto..."

Post "$base/proyecto" @{ clave="nombre"; valor="PVZFUSIONMOD - Mod de Plants vs Zombies en Unity C#" }
Post "$base/proyecto" @{ clave="descripcion"; valor="Mod con sistema de FUSION: dos plantas colocadas una sobre otra se combinan en una planta hibrida definida por MixData. Mas de 60 plantas base, 50+ fusiones, zombies-planta y 78 tipos de proyectiles." }
Post "$base/proyecto" @{ clave="estructura"; valor="Plants en Scripts/Plants/, Bullets en Scripts/Bullets/, Zombies en Scripts/Zombies/, Creators en Scripts/Creators/, Otros en Scripts/Others/, UI en Scripts/UI/. Prefabs en Resources/plants/, Resources/bullet/prefabs/, Resources/zombies/" }
Post "$base/proyecto" @{ clave="herencia_plantas"; valor="Todas las plantas heredan de Plant. Disparadoras heredan de Shooter->Plant. Productoras heredan de Producer->Plant. Fusiones van en Scripts/Plants/_mixer/" }
Post "$base/proyecto" @{ clave="herencia_zombies"; valor="Todos los zombies heredan de Zombie. Zombies que disparan heredan de PeaShooterZ->Zombie. Zombies-planta van en Scripts/Zombies/plantzombie/" }
Post "$base/proyecto" @{ clave="factories"; valor="CreateBullet.Instance.SetBullet(), CreatePlant.Instance.SetPlant(), CreateZombie.Instance.SetZombie(), CreateCoin.Instance.SetCoin(), CreateMeteor. Son singletons, nunca crear nuevos." }
Post "$base/proyecto" @{ clave="grid_sistema"; valor="Board gestiona el tablero. board.plantArray, board.zombieArray, board.bulletArray, board.coinArray. Posicion mundo via Mouse.GetBoxXFromColumn(col) y Mouse.GetBoxYFromRow(row). NUNCA hardcodear posiciones Y." }
Post "$base/proyecto" @{ clave="prefabs"; valor="GameAPP.plantPrefab[], GameAPP.bulletPrefab[], GameAPP.zombiePrefab[] son arrays globales. Resources.Load usa rutas RELATIVAS a /Resources/ sin 'Assets/' delante. Ej: Resources.Load<GameObject>('plants/peashooter/peashooter')" }
Post "$base/proyecto" @{ clave="sistema_fusiones"; valor="MixData.data[tipoA, tipoB] = tipoResultado. La tabla es simetrica: siempre agregar data[A,B] y data[B,A]. IDs de fusion: 1000-1099 primer nivel, 1100+ nivel alto. Mouse consulta MixData al soltar planta sobre otra." }
Post "$base/proyecto" @{ clave="ids_plantas_base"; valor="0=Peashooter, 1=Sunflower, 2=CherryBomb, 3=WallNut, 4=PotatoMine, 5=Chomper, 6=SmallPuff, 7=FumeShroom, 8=HypnoShroom, 9=ScaredyShroom, 10=IceShroom, 11=DoomShroom, 13=Squash, 14=ThreePeater, 16=Jalapeno" }
Post "$base/proyecto" @{ clave="ids_balas_principales"; valor="0=Pea, 1=Cherry, 3=SuperCherry, 9=Puff, 11=IronPea, 15=SnowPea, 23=Doom, 24=IceDoom, 28=Squash, 37=Minihypnoshroom, 47=Doomrune, 48=IceRune, 49=FireRune, 50=CherryRune, 75=Supersun, 77=Pankeik" }
Post "$base/proyecto" @{ clave="escenas"; valor="SceneType: 0=Day, 1=Night, 2=Pool, 3=NightPool, 4=Roof, 6=Day_6 (6 filas), 8=Jurassic, 9=CandyWorld. Filas de agua: roadType[row]==1." }

# ── CONVENCIONES ────────────────────────────────────────────
Write-Host "`n[2/4] Convenciones de codigo..."

Post "$base/convenciones" @{ titulo="dano_zombies"; contenido="NUNCA usar zombie.theHealth -= X directamente. SIEMPRE llamar zombie.TakeDamage(damageType, damage). Tipos: 0=normal, 1=fuego, 2=hielo. Omitir esto saltea armaduras, difficulty scaling e isJalaed." }
Post "$base/convenciones" @{ titulo="dano_plantas"; contenido="NUNCA usar plant.thePlantHealth -= X. SIEMPRE llamar plant.TakeDamage(damage). Omitir esto saltea TwinSunflowerShield y ProtectedPlantMarker." }
Post "$base/convenciones" @{ titulo="punto_disparo"; contenido="Siempre buscar el punto de disparo con transform.Find('Shoot').position. El objeto 'Shoot' debe existir en el prefab. Agregar +0.1f en X al instanciar la bala." }
Post "$base/convenciones" @{ titulo="patron_animshoot"; contenido="Vector3 pos = transform.Find('Shoot').position; GameObject bullet = board.GetComponent<CreateBullet>().SetBullet(pos.x+0.1f, pos.y, thePlantRow, bulletType, movinway); bullet.GetComponent<Bullet>().theBulletDamage = BulletDmg; GameAPP.PlaySound(Random.Range(3,5));" }
Post "$base/convenciones" @{ titulo="no_object_pooling"; contenido="El proyecto NO usa Object Pooling. Todo es Instantiate/Destroy. No introducir pooling sin refactorizar todo el sistema." }
Post "$base/convenciones" @{ titulo="no_scriptableobjects"; contenido="El proyecto NO usa ScriptableObjects. La configuracion esta hardcodeada en los scripts. No agregar ScriptableObjects." }
Post "$base/convenciones" @{ titulo="verificar_gamestatus"; contenido="Siempre verificar theGameStatus == 0 antes de ejecutar logica de juego en Update(). 0=jugando, otros valores=pausado/perdido/ganado." }
Post "$base/convenciones" @{ titulo="registrar_nueva_planta"; contenido="Para nueva planta: 1) Clase hereda de Plant/Shooter/Producer. 2) Registrar ID en GameAPP.plantPrefab[ID]. 3) Si es fusion, agregar ambas direcciones en MixData. 4) Prefab en Resources/plants/ o Resources/plants/_mixer/." }
Post "$base/convenciones" @{ titulo="registrar_nueva_bala"; contenido="Para nueva bala: 1) Clase hereda de Bullet. 2) Agregar al enum BulletType con ID unico. 3) Agregar case en CreateBullet.AddUniqueComponent(). 4) Prefab en Resources/bullet/prefabs/. 5) Registrar en GameAPP.bulletPrefab[ID]." }
Post "$base/convenciones" @{ titulo="zombie_mindcontrol"; contenido="Si zombie.isMindControlled=true: NO marcar bala como isZombieBullet (puede herir zombies), invertir X del disparo para que tire hacia la derecha. Zombie aparece con color morado en layer MindControlledZombie." }
Post "$base/convenciones" @{ titulo="resources_load"; contenido="Resources.Load usa rutas RELATIVAS a /Resources/. CORRECTO: Resources.Load<GameObject>('plants/peashooter/peashooter'). INCORRECTO: Resources.Load<GameObject>('Assets/PVZFUSIONMOD/Assets/Resources/plants/...'). Siempre verificar null antes de usar." }
Post "$base/convenciones" @{ titulo="producer_sol"; contenido="Plantas productoras llaman CreateCoin.Instance.SetCoin(thePlantColumn, thePlantRow, 0, 0) para generar sol. El tipo 0 es sol estandar. Heredar de Producer, sobreescribir ProduceSun()." }

# ── RESUMEN DE SCRIPTS CLAVE ─────────────────────────────────
Write-Host "`n[3/4] Resumen de scripts clave..."

Post "$base/aprender" @{
    nombre = "Plant.cs (resumen)"
    contenido = ""
    resumen = "Clase base de todas las plantas. Variables: thePlantType(int ID), thePlantHealth/thePlantMaxHealth, thePlantRow/thePlantColumn, thePlantAttackInterval/thePlantAttackCountDown, board(Board), zombieList, targetZombie. Flags: isPot,isLily,isNut,IsMine,IsChomper,IsProducer,IsPult,isinmortal. Metodos: TakeDamage(int damage), SearchZombie(), PlantShootUpdate(), Die(reason), Crashed(), Recover(health), SetCold(time), Booster(), Booster1()."
}

Post "$base/aprender" @{
    nombre = "Shooter.cs (resumen)"
    contenido = ""
    resumen = "Hereda de Plant. Base para plantas disparadoras. Llama PlantShootUpdate() cada frame si theGameStatus==0. Variable: dreamTime (espera inicial). Metodo abstracto AnimShoot() que cada subclase implementa para crear su bala. NO sabe que bala usa, solo cuando disparar."
}

Post "$base/aprender" @{
    nombre = "Bullet.cs (resumen)"
    contenido = ""
    resumen = "Clase base de proyectiles. Variables: theBulletType, theBulletDamage(default=20), theBulletRow, theMovingWay(0=recto), isZombieBullet, fireLevel, isHot, canHitZombies, useZigZag. Al impactar llama zombie.TakeDamage(damageType, theBulletDamage). damageType: 0=normal, 1=fuego, 2=hielo."
}

Post "$base/aprender" @{
    nombre = "Zombie.cs (resumen)"
    contenido = ""
    resumen = "Clase base de zombies. Variables: theZombieType, theZombieRow, theHealth(float), theStatus(0=normal,1=sin cabeza,3=aplastado,9=muerto), theSpeed/theOriginSpeed, theAttackDamage(default=50), isMindControlled, isJalaed(x1.5 dano), theFreezeCountDown, freezeLevel. TakeDamage(damageType, damage): 0=normal reduce cuerpo/armadura, 1=fuego ignora escudos. Sistema de armaduras: theFirstArmor, theSecondArmor."
}

Post "$base/aprender" @{
    nombre = "MixData.cs (resumen)"
    contenido = ""
    resumen = "Tabla de todas las fusiones. data[tipoA, tipoB] = tipoResultado. Si resultado==0, no se pueden fusionar. Siempre agregar ambas direcciones: data[A,B]=C y data[B,A]=C. Ejemplo: data[0,2]=1004 (Peashooter+CherryBomb=CherryShooter). IDs 1000+ son fusiones primer nivel, 1100+ fusiones avanzadas."
}

Post "$base/aprender" @{
    nombre = "CreateBullet.cs (resumen)"
    contenido = ""
    resumen = "Factory de balas. Singleton: CreateBullet.Instance o board.GetComponent<CreateBullet>(). Metodo: SetBullet(float x, float y, int row, int bulletType, int movingWay) -> GameObject. Instancia GameAPP.bulletPrefab[bulletType] y AddComponent la clase C# via AddUniqueComponent(). 78 tipos definidos en enum BulletType. Para nueva bala: agregar al enum + case en AddUniqueComponent() + prefab + GameAPP registro."
}

Post "$base/aprender" @{
    nombre = "CreatePlant.cs (resumen)"
    contenido = ""
    resumen = "Factory de plantas. Singleton: CreatePlant.Instance. Metodo: SetPlant(int col, int row, int seedType) -> GameObject. Valida coordenadas (col 0-9, row 0 a roadNum-1), calcula posicion mundo via Mouse.GetBoxXFromColumn/Row, instancia GameAPP.plantPrefab[seedType], registra en board.plantArray. Metodo especial SetPlantInAlmanac() para almanaque (sin logica de juego)."
}

# ── VERIFICACION ─────────────────────────────────────────────
Write-Host "`n[4/4] Verificando contexto cargado..."
try {
    $ctx = Invoke-RestMethod -Uri "$base/contexto" -Method GET
    $len = $ctx.contexto.Length
    Write-Host "  Contexto activo: $len caracteres" -ForegroundColor Green
} catch {
    Write-Host "  No se pudo verificar: $_" -ForegroundColor Yellow
}

Write-Host "`n== Listo! Cognia Dev ahora conoce PVZFUSIONMOD ==" -ForegroundColor Cyan
Write-Host "Desde Unity (Window > Cognia Dev) ya podes pedir cosas como:"
Write-Host "  - 'Crea una planta fusionada de Sunflower y IceShroom que produzca sol frio'"
Write-Host "  - 'Agrega una bala que congele y haga splash en area'"
Write-Host "  - 'Crea un zombie que dispare cherry y tenga doble armadura'"
