# PLAN — Cabinet Médical (Maroc) : étude approfondie & architecture cible

> Document de référence. Contrat d'API : `hos_ma_front/API.md`. Périmètre MVP : `MVP-PLAN.md`.
> Benchmark concurrent : `etude-pratisoft.md`. Feuille de route opérationnelle : `TASKS.md`.

---

## 1. Objectif

Livrer un MVP fonctionnel de gestion de cabinet médical (Maroc) : **Django REST Framework + Angular**,
avec dossier patient, agenda, ordonnances bilingues FR/AR, facturation CNOPS/CNSS/mutuelles, dashboard.
Conformité locale : CNOPS/CNSS/DGI, ordonnance FR/AR, loi 09-08.

Le **frontend est déjà construit** contre un contrat REST propre (voir `API.md`).
Le **backend actuel (`suivi_back_1`) ne respecte pas ce contrat** (API RPC legacy).
→ La stratégie est **contract-first** : on gèle `API.md` comme source de vérité et on fait converger le backend.

---

## 2. État des lieux

### 2.1 Frontend — `hos_ma_front/` (Angular 13, thème "cliniva")

Déjà en place :

- Auth JWT + interceptors (`core/service/auth.service.ts`, `core/interceptor/`).
- Guards par rôle (`core/guard/auth.guard.ts`), rôles `admin|doctor|assistant|patient` (`core/models/role.ts`).
- Écrans CRUD admin : cabinets, doctor, assistants, users, patients, patient-files, appointments,
  invoices, ordonnances, me.
- 4 écrans catalogue génériques pilotés par config (`admin/catalogue/catalogue.config.ts`) :
  specialites, medicaments, actes-demandes, actes-faits.
- Zones doctor / assistant / patient (routes montées sur les composants admin, role-adaptatifs).
- Mapping des endpoints attendus : `layout/sidebar/sidebar-items.ts:12-26`.

Manques front (voir détail §5) :

- Fiche patient à onglets (antécédents / allergies / observations ICD-10) : **absente**.
- Dashboards = **données mockées** (`doctor/dashboard/dashboard.component.ts:62-133`).
- Pas de PDF ordonnance/facture, pas d'agenda calendaire, patient area quasi vide.
- `fake-backend` encore branché (`app.module.ts:16,82`).

### 2.2 Backend — `suivi_back_1/` (Django/DRF legacy)

- Une seule app `cab_g`. Routage RPC (`suivi_back/urls.py:9-72`), pas de routeurs DRF.
- Modèles partiels et bugués (`cab_g/models.py`), pas de timestamps.
- Permissions : `IsAuthenticated` seul, pas de scoping cabinet fiable.
- `requirements.txt` vide, `tests.py` factice, `DEBUG=True`, `SECRET_KEY` en clair.

### 2.3 Documents

| Fichier | Rôle |
|---|---|
| `etude-pratisoft.md` | Benchmark fonctionnel (20+ spécialités, GDT/DICOM, RGPD) — inspiration v2 |
| `MVP-PLAN.md` | Cahier des charges MVP (6 modules, modèles, endpoints, DoD) |
| `hos_ma_front/API.md` | **Contrat d'API cible** (source de vérité) |
| `suivi_back_1/base donner.pdf` | Schéma BDD (non lisible par l'outil — à fournir) |

---

## 3. Diagnostic : décalage Front ↔ Back

| Sujet | Attendu (front) | Backend actuel | Impact |
|---|---|---|---|
| Style API | REST (`/api/patients/`, `/{id}/`, PATCH) | RPC (`create-/get-/update-/delete-`) | Bloquant |
| Auth | `/api/auth/token/`, `/api/auth/me/` (`role`,`cabinet_id`) | `/api/token/`, `hello/`, claims `groups` | Bloquant |
| Pagination | `{count,next,previous,results}` | aucune | Bloquant |
| Erreurs | `{error:{status,code,detail,fields}}` | DRF brut | Bloquant |
| Permissions | rôles + scoping cabinet | `IsAuthenticated` seul | Sévère |
| Timestamps | `created_at`/`updated_at` | absents | Sévère |
| Modèles MVP | Antécédent, Allergie, Observation, InvoiceItem, Payment, Medication FR/AR | absents/bugués | Bloquant |

Bugs backend localisés :

- `models.py:99` `Ordonnance.appointment` → FK vers `Patient` (doit être `Appointment`).
- `models.py:115` `Invoice.__str__` référence `self.status` inexistant → crash.
- `views.py:246,385` `Patient.values_list('appointment')` invalide.
- `views.py:411,415` confusion `recipient` (User) / cabinet (int).
- `views.py:88,748` `User.objects.last()` pour récupérer l'utilisateur créé (faux/race).
- `settings.py:12/16/134/139` secret, DEBUG, MEDIA_ROOT absolu, CORS ouvert.

---

## 4. Architecture cible

### 4.1 Stack

- **Back** : Django 4.x, DRF, SimpleJWT, drf-spectacular (OpenAPI), django-cors-headers,
  Pillow (images), reportlab ou weasyprint (PDF), SQLite (dev) / PostgreSQL (prod).
- **Front** : Angular 13 (existant), Angular Material, environnement `restUrl`.
- **Format d'échange** : JSON REST paginé, erreurs structurées, JWT Bearer.

### 4.2 Apps Django

| App | Contenu |
|---|---|
| `accounts` | User custom + `role`, Cabinet, Specialite, permissions, JWT, `/me/` |
| `patients` | Patient, Antecedent, Allergie, Observation (ICD-10), PatientFile |
| `appointments` | Appointment (start/end, statuts, anti-chevauchement, agenda) |
| `prescriptions` | Medicament (FR/AR), Ordonnance, OrdonnanceLine |
| `billing` | Invoice, InvoiceItem, Payment, reliquats |
| `staff` (option) | Doctor, Assistant (profils liés à User) |
| `core` | health, pagination, exceptions, permissions, mixins cabinet |

### 4.3 Modèle de données cible (à créer/migrer)

```
User(id, email, role[ADMIN|DOCTOR|ASSISTANT|PATIENT], first/last, is_active, cabinet?)
Cabinet(id, name, number, address, logo, header_fr, header_ar, created_at, updated_at)
Specialite(id, name)

Doctor(id, user, cabinet, img, inp, gender, phone, address, specialite, ts)
Assistant(id, user, cabinet, img, cin, gender, phone, address, ts)

Patient(id, cabinet, cin, img, firstname, lastname, gender, age, phone, address,
        child, assurance[CNOPS|CNSS|MUTUELLE|AUCUNE], numero_adherent, ts)
Antecedent(id, patient, type, description, ts)
Allergie(id, patient, substance, severity, ts)
Observation(id, patient, praticien, date, motif, diagnostic_icd10, notes, version, ts)
PatientFile(id, patient, file, uploaded_at)

Appointment(id, patient, praticien, cabinet, date, start, end, motif, status, notes, payed, ts)
Medicament(id, cabinet, name_fr, name_ar, form, dosage, ts)
Ordonnance(id, patient, appointment, praticien, cabinet, type, notes_fr, notes_ar, ts)
OrdonnanceLine(id, ordonnance, medicament, dosage_fr, dosage_ar, duration, quantity)
Invoice(id, patient, appointment, number, date, total, part_organisme, part_patient,
        status[BROUILLON|EMISE|PAYEE|PARTIELLE|IMPAYEE], ts)
InvoiceItem(id, invoice, acte, code_acte, quantity, unit_price)
Payment(id, invoice, amount, date, mode[ESPECES|CARTE|CHEQUE|VIREMENT])
```

> Tout modèle porte `created_at`/`updated_at` (mixine `TimeStampedModel`).

### 4.4 Contrat d'API

`API.md` est **gelé**. Endpoints clés :

```
POST /api/auth/token/ | /refresh/ | /verify/ ; GET /api/auth/me/
CRUD /api/cabinets/ /specialites/ /doctors/ /assistants/ /users/
CRUD /api/patients/ + /api/patients/{id}/dossier/
CRUD /api/patient-files/  (multipart, max 5 Mo)
CRUD /api/appointments/ + /api/appointments/agenda/?date=&praticien=
CRUD /api/ordonnances/ + /api/ordonnances/{id}/pdf/
CRUD /api/invoices/ + /unpaid/ + /{id}/payments/ + /{id}/pdf/
GET  /api/dashboard/stats/
GET  /api/health/ /schema/ /docs/ /redoc/
```

Règles transverses : JWT partout, scoping cabinet depuis le token, pagination 50 (max 200),
filtres `search`/`ordering`/`page`, erreurs structurées.

---

## 5. Stratégie de travail parallèle (front / back)

Objectif : les deux voies avancent **en même temps** sans se bloquer grâce au **contrat gelé**.

1. **Contract-first** : `API.md` figé. Le back implémente, le front consomme.
2. **OpenAPI vivant** : `drf-spectacular` expose `/api/schema/`. On génère les types TS et/ou un mock
   pour que le front ne dépende jamais d'un endpoint non encore livré.
3. **Mock côté front** : remplacer `fake-backend` par un mock généré depuis OpenAPI (ou `json-server`)
   pendant le développement, puis basculer sur le vrai back.
4. **Contrats de test partagés** : jeux d'exemples requête/réponse dans `API.md` → utilisés comme
   fixtures de test back ET comme données mock front.
5. **Une seule vérité de schéma** : les noms de champs viennent de `API.md` ; tout écart est un bug.

Découpage des rôles :

- **Voie Back** : auth/permissions, modèles, routeurs, pagination, PDF, stats, tests, sécurité.
- **Voie Front** : fiche patient (dossier), câblage dashboard, aperçu PDF, agenda calendaire,
  nettoyage (fake-backend, env prod), i18n FR/AR.

---

## 6. Sécurité & conformité

- Secrets via variables d'environnement ; `DEBUG=False` en prod ; `ALLOWED_HOSTS` restreints.
- `CORS_ALLOWED_ORIGINS` explicites ; HTTPS en prod.
- Mots de passe : validateurs Django ; JWT court + refresh.
- Permissions : secrétaire ≠ écriture dossier clinique ; admin vs staff (scoping cabinet).
- Mention loi 09-08 sur les écrans patients + consentement simple (MVP) → consentement horodaté (v2).
- Journaux d'accès sur les données médicales.

---

## 7. Qualité & tests

- **Back** : tests par app (auth, permissions, scoping cabinet, anti-chevauchement RDV, calcul reliquats,
  génération PDF). Objectif : ≥ 70 % sur la logique métier.
- **Front** : `ng lint`, build prod sans erreur, tests unitaires sur services clés + guards.
- **E2E** : parcours des critères d'acceptation `MVP-PLAN.md §6` (Protractor/Cypress).
- CI : lint + tests back/front sur chaque PR.

---

## 8. Risques

| Risque | Impact | Mitigation |
|---|---|---|
| Back non aligné sur contrat | Bloquant | Contract-first + OpenAPI + mocks |
| Modèles MVP absents | Élevé | Lots dédiés (voir `TASKS.md`) |
| PDF AR/FR (RTL) | Moyen | Choisir moteur tôt (weasyprint si HTML/CSS) |
| Sécurité legacy (secret/DEBUG) | Élevé | Lot sécurité prioritaire |
| Dépendances Angular 13 anciennes | Moyen | Geler versions, build prod vérifié |
| `base donner.pdf` non lisible | Faible | Fournir le schéma pour validation |

---

## 9. Definition of Done (global)

- [ ] Backend conforme à `API.md`, pagination + erreurs + permissions + scoping cabinet.
- [ ] Critères d'acceptation `MVP-PLAN.md §6` validés de bout en bout.
- [ ] Front sans `fake-backend`, envs dev/prod corrects, build prod OK.
- [ ] Dossier médical (antécédents/allergies/observations) opérationnel.
- [ ] Ordonnance FR/AR PDF + facture PDF.
- [ ] Dashboard alimenté par `/api/dashboard/stats/`.
- [ ] Tests back ≥ 70 %, lint front OK, seed de démo `MVP-PLAN.md §7`.
- [ ] Sécurité prod (secret, DEBUG, CORS, HTTPS).
