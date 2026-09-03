# Backlog — référentiels externes cités par le guide MCO

*Ouvert le 2026-09-03 (lot 4 du chantier B, cas POL-01).*

Certaines consignes du guide s'appuient sur des **référentiels
externes** qu'elles citent sans les reproduire. Premier cas rencontré :
l'article IDENTIFICATION DU POLYHANDICAP LOURD (GM2026-V-POL-01) exige
« un code au moins de chacune des quatre listes » — les quatre listes
de codes CIM-10 (déficiences mentales sévères, troubles moteurs,
mobilité réduite, restrictions extrêmes d'autonomie), élaborées sous le
contrôle de la SFP et de la SFNP, sont publiées sur le **site de
l'ATIH**, pas dans le guide.

Conséquence actuelle : POL-01 est une consigne **sans association**
(rapport `sans_code`) — la doctrine interdit d'inventer des cibles que
le texte ne nomme pas.

**Besoin futur** : le vérificateur de scénarios (recode-scenario) aura
besoin de ces listes pour évaluer la contrainte « un code de chacune
des quatre listes ». À faire, le moment venu :

1. récupérer les quatre listes sur le site de l'ATIH, **versionnées**
   (millésime + date de téléchargement + empreinte) ;
2. les intégrer comme référentiel externe séparé (patron
   `data/…/*_curated.csv` ou parquet dédié), jamais fondues dans les
   tables du guide ;
3. relier POL-01 à ce référentiel par un mécanisme à concevoir
   (l'association `rec_id → liste externe` n'existe pas dans le modèle
   actuel — proposition d'extension à arbitrer).

Autres cas du même type à guetter dans la suite de la file : listes de
germes, classifications d'actes, instructions citées en référence
(ex. ENF-01 : note technique DREES/DGS/DGOS 2021).
