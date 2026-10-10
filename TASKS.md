# TASKS — Feuille de route & suivi (Cabinet Médical Maroc)

> Base d'étude : `PLAN.md`. Contrat gelé : `hos_ma_front/API.md`. Périmètre : `MVP-PLAN.md`.
> Convention : `BE-xx` = backend, `FE-xx` = frontend, `OPS-xx` = infra/sécurité, `QA-xx` = tests.
> Estimation en **jours-homme (j)**. « Bloc » = dépendance à terminer avant de démarrer.

---

## 0. Vue d'ensemble (planning indicatif)

Hypothèse : **1 dev back + 1 dev front en parallèle** (voies BE et FE simultanées), QA en continu.
Chemin critique piloté par le backend (le front est déjà majoritairement livré).

| Phase | Semaine | Voie BE (j) | Voie FE (j) | Jalon |
|---|---|---|---|---|
| P0 Cadrage & contrat | S1 (0,5 j) | 0,5 | 0,5 | Contrat gelé + mocks OK |
| P1 Fondations back | S1 | 2 | — | App démarre, `/health/`, pagination |
| P2 Auth & rôles | S1–S2 | 2 | 1 | Login réel de bout en bout |
| P3 Référentiels & users | S2 | 2 | 0,5 | Écrans admin branchés |
| P4 Patients & dossier | S2–S3 | 3 | 2,5 | Dossier médical opérationnel |
| P5 Agenda | S3 | 2,5 | 2 | RDV + vue calendrier |
| P6 Ordonnances + PDF | S3–S4 | 3 | 1,5 | PDF FR/AR |
| P7 Facturation + PDF | S4 | 3 | 1,5 | Reliquats + paiements |
| P8 Dashboard & stats | S4 | 1,5 | 1 | KPIs réels |
| P9 Durcissement & déploiement | S4–S5 | 3 | 1,5 | Prod prête |

**Chemin critique ≈ 4 semaines.** Back ≈ 22,5 j ; Front ≈ 12 j (en parallèle, non bloquant après P0).

Diagramme texte :

```
S1        S2        S3        S4        S5
BE: P0-P1-P2------P3-P4-----------P5-P6---P7-P8-P9
FE: P0---P2---P3------P4--------------P5-P6-P7-P8-P9
QA: ............tests continus......................E2E
```

---

## 1. Phase 0 — Cadrage & contrat (0,5 j)

- [x] **OPS-01** Geler `API.md` comme référence unique ; documenter tout écart comme bug. (0,5 j)
- [x] **OPS-02** Mettre en place le dépôt mono-projet (front + back) ou garder 2 repos synchronisés. (0,5 j)
- [ ] **FE-01** Remplacer `fake-backend` par un mock généré depuis OpenAPI (ou `json-server`). (0,5 j)
      Réf : `hos_ma_front/src/app/app.module.ts:16,82`.

**DoD** : contrat figé ; le front démarre contre un mock respectant `API.md` ; plus aucune dépendance au back legacy.

---

## 2. Phase 1 — Fondations backend (2 j)

- [x] **BE-01** `requirements.txt` complet (Django, DRF, simplejwt, corsheaders, drf-spectacular, Pillow, reportlab/weasyprint). (0,2 j)
- [x] **BE-02** Settings découpés dev/prod via variables d'env (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `MEDIA_ROOT`). (0,5 j)
      Réf bug : `suivi_back_1/suivi_back/settings.py:12,16,134,139`.
- [x] **BE-03** `REST_FRAMEWORK` : pagination (`DEFAULT_PAGINATION_CLASS`, 50/max 200), auth JWT, renderer/exception custom. (0,4 j)
- [x] **BE-04** Handler d'exceptions → format `{error:{status,code,detail,fields}}`. (0,4 j)
- [x] **BE-05** Structure en apps : `core`, `accounts`, `patients`, `appointments`, `prescriptions`, `billing`. (0,3 j)
- [x] **BE-06** `core` : `TimeStampedModel`, mixin de scoping cabinet, permissions de base. (0,5 j)
- [x] **BE-07** Endpoints `/api/health/`, `/api/schema/`, `/api/docs/`, `/api/redoc/`. (0,3 j)

**DoD** : le serveur démarre, `/health/` répond, la pagination et les erreurs sont conformes, OpenAPI se génère.

---

## 3. Phase 2 — Auth & rôles (2 j BE / 1 j FE)

- [x] **BE-08** User custom (ou User + champ `role`) + Cabinet lié. (0,5 j)
- [x] **BE-09** `POST /api/auth/token/`, `/refresh/`, `/verify/`. (0,4 j)
- [x] **BE-10** `GET /api/auth/me/` → `{id, username, first/last, email, is_active, role, cabinet_id}`. (0,4 j)
- [x] **BE-11** Permissions par rôle (`IsAdmin`, `IsDoctor`, `IsCabinetStaff`) + scoping queryset cabinet. (0,5 j)
- [x] **BE-12** Seed rôles/groupes + superuser admin. (0,2 j)
- [ ] **FE-02** Basculer `auth.service.ts` sur le vrai back ; corriger `error.interceptor.ts` (refresh). (0,5 j)
      Réf : `core/service/auth.service.ts:55,77,90`, `core/interceptor/error.interceptor.ts:31`.
- [ ] **FE-03** Guards/redirections par rôle finalisés. (0,5 j) Réf : `core/guard/auth.guard.ts`.

**Bloc** : BE-09/10 avant FE-02.
**DoD** : un médecin, une secrétaire et un admin se connectent ; `/me/` retourne le bon rôle ; accès interdits refusés.

---

## 4. Phase 3 — Référentiels & utilisateurs (2 j BE / 0,5 j FE)

- [x] **BE-13** `Cabinet` + `/api/cabinets/` (CRUD, `created_at/updated_at`). (0,4 j)
- [x] **BE-14** `Specialite` + `/api/specialites/` (catalogue global). (0,2 j)
- [x] **BE-15** `/api/medicaments/`, `/api/actes-demandes/`, `/api/actes-faits/` (scopés cabinet). (0,6 j)
- [x] **BE-16** `/api/doctors/`, `/api/assistants/` avec `user`, `cabinet_name`, `specialiste_name`, timestamps. (0,5 j)
- [x] **BE-17** `/api/users/` (lecture seule). (0,3 j)
- [ ] **FE-04** Vérifier le mapping des 4 catalogues + écrans admin contre le vrai back. (0,5 j)
      Réf : `admin/catalogue/catalogue.config.ts:41-85`, `layout/sidebar/sidebar-items.ts:12-26`.

**DoD** : tous les écrans référentiels et le catalogue fonctionnent, pagination et filtres inclus.

---

## 5. Phase 4 — Patients & dossier médical (3 j BE / 2,5 j FE)

- [x] **BE-18** `Patient` conforme (`assurance`, `numero_adherent`, `cabinet_name`, timestamps) + `/api/patients/` (filtres, ordering, upload `img`). (0,8 j)
- [x] **BE-19** `/api/patient-files/` (multipart, max 5 Mo, `patient_name`, `download_url`). (0,5 j)
- [x] **BE-20** Modèles `Antecedent`, `Allergie`, `Observation` (ICD-10) + endpoints CRUD. (1 j)
- [x] **BE-21** `GET /api/patients/{id}/dossier/` (obs + antécédents + allergies). (0,7 j)
- [ ] **FE-05** Fiche patient à onglets (infos / antécédents / allergies / observations). (1,5 j)
      Réf : routes actuelles limitées à la liste `admin/patient/patient-routing.module.ts:6-15`.
- [ ] **FE-06** Formulaire observation avec sélecteur diagnostic ICD-10 + versionnage. (1 j)

**Bloc** : BE-18/20 avant FE-05.
**DoD** : création patient, saisie antécédents/allergies, observation avec diagnostic ICD-10, upload de pièce.

---

## 6. Phase 5 — Agenda / RDV (2,5 j BE / 2 j FE)

- [x] **BE-22** `Appointment` conforme (`start`, `end`, `motif`, `status`, `payed`, `patient_name`, timestamps). (0,7 j)
- [x] **BE-23** Anti-chevauchement (test correct, pas de `values_list('appointment')`). (0,6 j)
      Réf bug : `cab_g/views.py:246,385`.
- [x] **BE-24** `GET /api/appointments/agenda/?date=&praticien=` + `POST .../cancel/` (ou statut). (0,6 j)
- [x] **BE-25** Filtres `date`, `date_from`, `date_to`, `patient`, `payed`, `search`, `ordering`. (0,6 j)
- [ ] **FE-07** Vue calendrier jour/semaine (FullCalendar déjà installé). (1,5 j)
- [ ] **FE-08** Formulaire RDV + changement de statut. (0,5 j)

**DoD** : planifier un RDV sans conflit, changer son statut, vue calendaire fonctionnelle.

---

## 7. Phase 6 — Ordonnances + PDF FR/AR (3 j BE / 1,5 j FE)

- [x] **BE-26** `Medicament` FR/AR (`name_fr`, `name_ar`, `form`, `dosage`). (0,5 j)
- [x] **BE-27** `Ordonnance` + `OrdonnanceLine` ; corriger la FK `appointment` → **Appointment**. (0,8 j)
      Réf bug : `cab_g/models.py:99`.
- [x] **BE-28** `/api/ordonnances/` avec `medicaments_list`, `acte_demander`, `acte_fait`. (0,6 j)
- [x] **BE-29** `GET /api/ordonnances/{id}/pdf/` bilingue FR/AR (en-tête cabinet, bloc RTL). (1,1 j)
- [ ] **FE-09** Éditeur bilingue + aperçu PDF. (1,5 j)
      Réf : `admin/ordonnance/ordonnance.model.ts:24-38`.

**DoD** : ordonnance bilingue imprimable avec en-tête cabinet, PDF téléchargeable.

---

## 8. Phase 7 — Facturation (3 j BE / 1,5 j FE)

- [x] **BE-30** `Invoice` + `InvoiceItem` + `Payment` (part organisme/patient, statuts). (1 j)
- [x] **BE-31** Corriger `Invoice.__str__` (`self.status` inexistant) + `/api/invoices/`. (0,4 j)
      Réf bug : `cab_g/models.py:115`.
- [x] **BE-32** `/api/invoices/unpaid/` + `POST /api/invoices/{id}/payments/`. (0,6 j)
- [x] **BE-33** `GET /api/invoices/{id}/pdf/` (en-tête, ventilation). (0,8 j)
- [x] **BE-34** Calcul reliquats (patient + organisme) et statuts dérivés. (0,4 j)
- [ ] **FE-10** Écran facturation : devis, paiement, reliquat, impression. (1,5 j)

**DoD** : facture avec part CNOPS/CNSS, paiement enregistré, reliquat affiché, PDF.

---

## 9. Phase 8 — Dashboard & stats (1,5 j BE / 1 j FE)

- [ ] **BE-35** `GET /api/dashboard/stats/` (patients du mois, RDV du jour, CA, reliquats). (1,5 j)
- [ ] **FE-11** Brancher les dashboards sur l'API (remplacer les mocks). (1 j)
      Réf mock : `doctor/dashboard/dashboard.component.ts:62-133`.

**DoD** : le tableau de bord affiche des KPIs réels.

---

## 10. Phase 9 — Durcissement, tests, déploiement (3 j BE / 1,5 j FE)

- [ ] **QA-01** Tests back : auth, permissions, scoping cabinet, chevauchement, reliquats, PDF. Objectif ≥ 70 %. (1,5 j)
- [ ] **BE-36** Remplacer `tests.py` factice ; seed de démo conforme `MVP-PLAN.md §7`. (0,7 j)
- [ ] **OPS-03** Sécurité prod : `DEBUG=False`, secrets, CORS restreint, HTTPS. (0,5 j)
- [ ] **OPS-04** Docker compose full-stack (front + back) ; corriger `render.yaml` / `environment.prod.ts`. (0,5 j)
      Réf : `hos_ma_front/environments/environment.prod.ts:10-11`.
- [ ] **FE-12** `ng lint` + build prod sans erreur ; retirer `fake-backend` résiduel. (0,5 j)
- [ ] **QA-02** E2E des critères d'acceptation `MVP-PLAN.md §6`. (1 j)
- [ ] **OPS-05** README racine (lancement front/back) + `.env.example`. (0,5 j)

**DoD** : prod déployable, tests verts, documentation de lancement.

---

## 11. Backlog v2 (hors MVP — inspiré `etude-pratisoft.md`)

- [ ] 2FA / SSO ; multi-cabinets ; SMS/WhatsApp/Email (rappels RDV).
- [ ] Interactions médicamenteuses ; exports DGI ; rétrocessions.
- [ ] Interopérabilité DICOM/GDT ; imagerie ; modules spécialités (cardio, dentaire, etc.).
- [ ] Consentement patient numérique horodaté ; parcours patient tablette.
- [ ] Chiffrement au repos + sauvegarde/cloud.

---

## 12. Suivi du chemin critique (à cocher au fil de l'eau)

- [ ] P0 Contrat gelé + mocks
- [x] P1 Back démarre + pagination/erreurs
- [x] P2 Auth bout-en-bout
- [x] P3 Référentiels branchés
- [x] P4 Dossier médical
- [x] P5 Agenda
- [x] P6 Ordonnances + PDF
- [x] P7 Facturation + PDF
- [ ] P8 Dashboard
- [ ] P9 Prod + tests + doc
