# TASKS â€” Feuille de route & suivi (Cabinet MÃ©dical Maroc)

> Base d'Ã©tude : `PLAN.md`. Contrat gelÃ© : `hos_ma_front/API.md`. PÃ©rimÃ¨tre : `MVP-PLAN.md`.
> Convention : `BE-xx` = backend, `FE-xx` = frontend, `OPS-xx` = infra/sÃ©curitÃ©, `QA-xx` = tests.
> Estimation en **jours-homme (j)**. Â« Bloc Â» = dÃ©pendance Ã  terminer avant de dÃ©marrer.

---

## 0. Vue d'ensemble (planning indicatif)

HypothÃ¨se : **1 dev back + 1 dev front en parallÃ¨le** (voies BE et FE simultanÃ©es), QA en continu.
Chemin critique pilotÃ© par le backend (le front est dÃ©jÃ  majoritairement livrÃ©).

| Phase | Semaine | Voie BE (j) | Voie FE (j) | Jalon |
|---|---|---|---|---|
| P0 Cadrage & contrat | S1 (0,5 j) | 0,5 | 0,5 | Contrat gelÃ© + mocks OK |
| P1 Fondations back | S1 | 2 | â€” | App dÃ©marre, `/health/`, pagination |
| P2 Auth & rÃ´les | S1â€“S2 | 2 | 1 | Login rÃ©el de bout en bout |
| P3 RÃ©fÃ©rentiels & users | S2 | 2 | 0,5 | Ã‰crans admin branchÃ©s |
| P4 Patients & dossier | S2â€“S3 | 3 | 2,5 | Dossier mÃ©dical opÃ©rationnel |
| P5 Agenda | S3 | 2,5 | 2 | RDV + vue calendrier |
| P6 Ordonnances + PDF | S3â€“S4 | 3 | 1,5 | PDF FR/AR |
| P7 Facturation + PDF | S4 | 3 | 1,5 | Reliquats + paiements |
| P8 Dashboard & stats | S4 | 1,5 | 1 | KPIs rÃ©els |
| P9 Durcissement & dÃ©ploiement | S4â€“S5 | 3 | 1,5 | Prod prÃªte |

**Chemin critique â‰ˆ 4 semaines.** Back â‰ˆ 22,5 j ; Front â‰ˆ 12 j (en parallÃ¨le, non bloquant aprÃ¨s P0).

Diagramme texte :

```
S1        S2        S3        S4        S5
BE: P0-P1-P2------P3-P4-----------P5-P6---P7-P8-P9
FE: P0---P2---P3------P4--------------P5-P6-P7-P8-P9
QA: ............tests continus......................E2E
```

---

## 1. Phase 0 â€” Cadrage & contrat (0,5 j)

- [x] **OPS-01** Geler `API.md` comme rÃ©fÃ©rence unique ; documenter tout Ã©cart comme bug. (0,5 j)
- [x] **OPS-02** Mettre en place le dÃ©pÃ´t mono-projet (front + back) ou garder 2 repos synchronisÃ©s. (0,5 j)
- [ ] **FE-01** Remplacer `fake-backend` par un mock gÃ©nÃ©rÃ© depuis OpenAPI (ou `json-server`). (0,5 j)
      RÃ©f : `hos_ma_front/src/app/app.module.ts:16,82`.

**DoD** : contrat figÃ© ; le front dÃ©marre contre un mock respectant `API.md` ; plus aucune dÃ©pendance au back legacy.

---

## 2. Phase 1 â€” Fondations backend (2 j)

- [x] **BE-01** `requirements.txt` complet (Django, DRF, simplejwt, corsheaders, drf-spectacular, Pillow, reportlab/weasyprint). (0,2 j)
- [x] **BE-02** Settings dÃ©coupÃ©s dev/prod via variables d'env (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `MEDIA_ROOT`). (0,5 j)
      RÃ©f bug : `suivi_back_1/suivi_back/settings.py:12,16,134,139`.
- [x] **BE-03** `REST_FRAMEWORK` : pagination (`DEFAULT_PAGINATION_CLASS`, 50/max 200), auth JWT, renderer/exception custom. (0,4 j)
- [x] **BE-04** Handler d'exceptions â†’ format `{error:{status,code,detail,fields}}`. (0,4 j)
- [x] **BE-05** Structure en apps : `core`, `accounts`, `patients`, `appointments`, `prescriptions`, `billing`. (0,3 j)
- [x] **BE-06** `core` : `TimeStampedModel`, mixin de scoping cabinet, permissions de base. (0,5 j)
- [x] **BE-07** Endpoints `/api/health/`, `/api/schema/`, `/api/docs/`, `/api/redoc/`. (0,3 j)

**DoD** : le serveur dÃ©marre, `/health/` rÃ©pond, la pagination et les erreurs sont conformes, OpenAPI se gÃ©nÃ¨re.

---

## 3. Phase 2 â€” Auth & rÃ´les (2 j BE / 1 j FE)

- [x] **BE-08** User custom (ou User + champ `role`) + Cabinet liÃ©. (0,5 j)
- [x] **BE-09** `POST /api/auth/token/`, `/refresh/`, `/verify/`. (0,4 j)
- [x] **BE-10** `GET /api/auth/me/` â†’ `{id, username, first/last, email, is_active, role, cabinet_id}`. (0,4 j)
- [x] **BE-11** Permissions par rÃ´le (`IsAdmin`, `IsDoctor`, `IsCabinetStaff`) + scoping queryset cabinet. (0,5 j)
- [x] **BE-12** Seed rÃ´les/groupes + superuser admin. (0,2 j)
- [ ] **FE-02** Basculer `auth.service.ts` sur le vrai back ; corriger `error.interceptor.ts` (refresh). (0,5 j)
      RÃ©f : `core/service/auth.service.ts:55,77,90`, `core/interceptor/error.interceptor.ts:31`.
- [ ] **FE-03** Guards/redirections par rÃ´le finalisÃ©s. (0,5 j) RÃ©f : `core/guard/auth.guard.ts`.

**Bloc** : BE-09/10 avant FE-02.
**DoD** : un mÃ©decin, une secrÃ©taire et un admin se connectent ; `/me/` retourne le bon rÃ´le ; accÃ¨s interdits refusÃ©s.

---

## 4. Phase 3 â€” RÃ©fÃ©rentiels & utilisateurs (2 j BE / 0,5 j FE)

- [x] **BE-13** `Cabinet` + `/api/cabinets/` (CRUD, `created_at/updated_at`). (0,4 j)
- [x] **BE-14** `Specialite` + `/api/specialites/` (catalogue global). (0,2 j)
- [x] **BE-15** `/api/medicaments/`, `/api/actes-demandes/`, `/api/actes-faits/` (scopÃ©s cabinet). (0,6 j)
- [x] **BE-16** `/api/doctors/`, `/api/assistants/` avec `user`, `cabinet_name`, `specialiste_name`, timestamps. (0,5 j)
- [x] **BE-17** `/api/users/` (lecture seule). (0,3 j)
- [ ] **FE-04** VÃ©rifier le mapping des 4 catalogues + Ã©crans admin contre le vrai back. (0,5 j)
      RÃ©f : `admin/catalogue/catalogue.config.ts:41-85`, `layout/sidebar/sidebar-items.ts:12-26`.

**DoD** : tous les Ã©crans rÃ©fÃ©rentiels et le catalogue fonctionnent, pagination et filtres inclus.

---

## 5. Phase 4 â€” Patients & dossier mÃ©dical (3 j BE / 2,5 j FE)

- [x] **BE-18** `Patient` conforme (`assurance`, `numero_adherent`, `cabinet_name`, timestamps) + `/api/patients/` (filtres, ordering, upload `img`). (0,8 j)
- [x] **BE-19** `/api/patient-files/` (multipart, max 5 Mo, `patient_name`, `download_url`). (0,5 j)
- [x] **BE-20** ModÃ¨les `Antecedent`, `Allergie`, `Observation` (ICD-10) + endpoints CRUD. (1 j)
- [x] **BE-21** `GET /api/patients/{id}/dossier/` (obs + antÃ©cÃ©dents + allergies). (0,7 j)
- [ ] **FE-05** Fiche patient Ã  onglets (infos / antÃ©cÃ©dents / allergies / observations). (1,5 j)
      RÃ©f : routes actuelles limitÃ©es Ã  la liste `admin/patient/patient-routing.module.ts:6-15`.
- [ ] **FE-06** Formulaire observation avec sÃ©lecteur diagnostic ICD-10 + versionnage. (1 j)

**Bloc** : BE-18/20 avant FE-05.
**DoD** : crÃ©ation patient, saisie antÃ©cÃ©dents/allergies, observation avec diagnostic ICD-10, upload de piÃ¨ce.

---

## 6. Phase 5 â€” Agenda / RDV (2,5 j BE / 2 j FE)

- [x] **BE-22** `Appointment` conforme (`start`, `end`, `motif`, `status`, `payed`, `patient_name`, timestamps). (0,7 j)
- [x] **BE-23** Anti-chevauchement (test correct, pas de `values_list('appointment')`). (0,6 j)
      RÃ©f bug : `cab_g/views.py:246,385`.
- [x] **BE-24** `GET /api/appointments/agenda/?date=&praticien=` + `POST .../cancel/` (ou statut). (0,6 j)
- [x] **BE-25** Filtres `date`, `date_from`, `date_to`, `patient`, `payed`, `search`, `ordering`. (0,6 j)
- [ ] **FE-07** Vue calendrier jour/semaine (FullCalendar dÃ©jÃ  installÃ©). (1,5 j)
- [ ] **FE-08** Formulaire RDV + changement de statut. (0,5 j)

**DoD** : planifier un RDV sans conflit, changer son statut, vue calendaire fonctionnelle.

---

## 7. Phase 6 â€” Ordonnances + PDF FR/AR (3 j BE / 1,5 j FE)

- [x] **BE-26** `Medicament` FR/AR (`name_fr`, `name_ar`, `form`, `dosage`). (0,5 j)
- [x] **BE-27** `Ordonnance` + `OrdonnanceLine` ; corriger la FK `appointment` â†’ **Appointment**. (0,8 j)
      RÃ©f bug : `cab_g/models.py:99`.
- [x] **BE-28** `/api/ordonnances/` avec `medicaments_list`, `acte_demander`, `acte_fait`. (0,6 j)
- [x] **BE-29** `GET /api/ordonnances/{id}/pdf/` bilingue FR/AR (en-tÃªte cabinet, bloc RTL). (1,1 j)
- [ ] **FE-09** Ã‰diteur bilingue + aperÃ§u PDF. (1,5 j)
      RÃ©f : `admin/ordonnance/ordonnance.model.ts:24-38`.

**DoD** : ordonnance bilingue imprimable avec en-tÃªte cabinet, PDF tÃ©lÃ©chargeable.

---

## 8. Phase 7 â€” Facturation (3 j BE / 1,5 j FE)

- [x] **BE-30** `Invoice` + `InvoiceItem` + `Payment` (part organisme/patient, statuts). (1 j)
- [x] **BE-31** Corriger `Invoice.__str__` (`self.status` inexistant) + `/api/invoices/`. (0,4 j)
      RÃ©f bug : `cab_g/models.py:115`.
- [x] **BE-32** `/api/invoices/unpaid/` + `POST /api/invoices/{id}/payments/`. (0,6 j)
- [x] **BE-33** `GET /api/invoices/{id}/pdf/` (en-tÃªte, ventilation). (0,8 j)
- [x] **BE-34** Calcul reliquats (patient + organisme) et statuts dÃ©rivÃ©s. (0,4 j)
- [ ] **FE-10** Ã‰cran facturation : devis, paiement, reliquat, impression. (1,5 j)

**DoD** : facture avec part CNOPS/CNSS, paiement enregistrÃ©, reliquat affichÃ©, PDF.

---

## 9. Phase 8 â€” Dashboard & stats (1,5 j BE / 1 j FE)

- [x] **BE-35** `GET /api/dashboard/stats/` (patients du mois, RDV du jour, CA, reliquats). (1,5 j)
- [ ] **FE-11** Brancher les dashboards sur l'API (remplacer les mocks). (1 j)
      RÃ©f mock : `doctor/dashboard/dashboard.component.ts:62-133`.

**DoD** : le tableau de bord affiche des KPIs rÃ©els.

---

## 10. Phase 9 â€” Durcissement, tests, dÃ©ploiement (3 j BE / 1,5 j FE)

- [ ] **QA-01** Tests back : auth, permissions, scoping cabinet, chevauchement, reliquats, PDF. Objectif â‰¥ 70 %. (1,5 j)
- [x] **BE-36** Remplacer `tests.py` factice ; seed de dÃ©mo conforme `MVP-PLAN.md Â§7`. (0,7 j)
- [ ] **OPS-03** SÃ©curitÃ© prod : `DEBUG=False`, secrets, CORS restreint, HTTPS. (0,5 j)
- [ ] **OPS-04** Docker compose full-stack (front + back) ; corriger `render.yaml` / `environment.prod.ts`. (0,5 j)
      RÃ©f : `hos_ma_front/environments/environment.prod.ts:10-11`.
- [ ] **FE-12** `ng lint` + build prod sans erreur ; retirer `fake-backend` rÃ©siduel. (0,5 j)
- [ ] **QA-02** E2E des critÃ¨res d'acceptation `MVP-PLAN.md Â§6`. (1 j)
- [ ] **OPS-05** README racine (lancement front/back) + `.env.example`. (0,5 j)

**DoD** : prod dÃ©ployable, tests verts, documentation de lancement.

---

## 11. Backlog v2 (hors MVP â€” inspirÃ© `etude-pratisoft.md`)

- [ ] 2FA / SSO ; multi-cabinets ; SMS/WhatsApp/Email (rappels RDV).
- [ ] Interactions mÃ©dicamenteuses ; exports DGI ; rÃ©trocessions.
- [ ] InteropÃ©rabilitÃ© DICOM/GDT ; imagerie ; modules spÃ©cialitÃ©s (cardio, dentaire, etc.).
- [ ] Consentement patient numÃ©rique horodatÃ© ; parcours patient tablette.
- [ ] Chiffrement au repos + sauvegarde/cloud.

---

## 12. Suivi du chemin critique (Ã  cocher au fil de l'eau)

- [ ] P0 Contrat gelÃ© + mocks
- [x] P1 Back dÃ©marre + pagination/erreurs
- [x] P2 Auth bout-en-bout
- [x] P3 RÃ©fÃ©rentiels branchÃ©s
- [x] P4 Dossier mÃ©dical
- [x] P5 Agenda
- [x] P6 Ordonnances + PDF
- [x] P7 Facturation + PDF
- [ ] P8 Dashboard
- [ ] P9 Prod + tests + doc
