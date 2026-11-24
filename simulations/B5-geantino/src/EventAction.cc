//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .  These *
// * include a list of copyright holders.                             *
// *                                                                  *
// * Neither the authors of this software system, nor their employing *
// * institutes,nor the agencies providing financial support for this *
// * work  make  any representation or  warranty, express or implied, *
// * regarding  this  software system or assume any liability for its *
// * use.  Please see the license in the file  LICENSE  and URL above *
// * for the full disclaimer and the limitation of liability.         *
// *                                                                  *
// * This  code  implementation is the result of  the  scientific and *
// * technical work of the GEANT4 collaboration.                      *
// * By using,  copying,  modifying or  distributing the software (or *
// * any work based  on the software)  you  agree  to acknowledge its *
// * use  in  resulting  scientific  publications,  and indicate your *
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
//
/// \file B5/src/EventAction.cc
/// \brief Implementation of the B5::EventAction class
///
/// Modificado pelo Geantino Labs (IFPR), nov/2026: sem histogramas/ntuple
/// ROOT; os mesmos valores vao para o RunAction (resultados.json).

#include "EventAction.hh"

#include "RunAction.hh"

#include "Constants.hh"
#include "DriftChamberHit.hh"
#include "EmCalorimeterHit.hh"
#include "HadCalorimeterHit.hh"
#include "HodoscopeHit.hh"

#include "G4Event.hh"
#include "G4HCofThisEvent.hh"
#include "G4ParticleDefinition.hh"
#include "G4PrimaryParticle.hh"
#include "G4PrimaryVertex.hh"
#include "G4RunManager.hh"
#include "G4SDManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4VHitsCollection.hh"

using std::array;
using std::vector;

namespace
{

// Utility function which finds a hit collection with the given Id
// and print warnings if not found
G4VHitsCollection* GetHC(const G4Event* event, G4int collId)
{
  auto hce = event->GetHCofThisEvent();
  if (!hce) {
    G4ExceptionDescription msg;
    msg << "No hits collection of this event found." << G4endl;
    G4Exception("EventAction::EndOfEventAction()", "Code001", JustWarning, msg);
    return nullptr;
  }

  auto hc = hce->GetHC(collId);
  if (!hc) {
    G4ExceptionDescription msg;
    msg << "Hits collection " << collId << " of this event not found." << G4endl;
    G4Exception("EventAction::EndOfEventAction()", "Code001", JustWarning, msg);
  }
  return hc;
}

}  // namespace

namespace B5
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

EventAction::EventAction(RunAction* runAction) : fRunAction(runAction)
{
  // Geantino Labs: o original imprimia todo evento (SetPrintProgress(1)).
  // Aqui fica desligado (0); /run/printProgress na macro liga de novo.
  G4RunManager::GetRunManager()->SetPrintProgress(0);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void EventAction::BeginOfEventAction(const G4Event*)
{
  // Find hit collections Ids by names (just once)
  // and save them in the data members of this class

  if (fHodHCID[0] == -1) {
    auto sdManager = G4SDManager::GetSDMpointer();

    // hits collections names
    array<G4String, kDim> hHCName = {{"hodoscope1/hodoscopeColl", "hodoscope2/hodoscopeColl"}};
    array<G4String, kDim> dHCName = {{"chamber1/driftChamberColl", "chamber2/driftChamberColl"}};
    array<G4String, kDim> cHCName = {
      {"EMcalorimeter/EMcalorimeterColl", "HadCalorimeter/HadCalorimeterColl"}};

    for (G4int iDet = 0; iDet < kDim; ++iDet) {
      // hit collections IDs
      fHodHCID[iDet] = sdManager->GetCollectionID(hHCName[iDet]);
      fDriftHCID[iDet] = sdManager->GetCollectionID(dHCName[iDet]);
      fCalHCID[iDet] = sdManager->GetCollectionID(cHCName[iDet]);
    }
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void EventAction::EndOfEventAction(const G4Event* event)
{
  //
  // Geantino Labs: as mesmas grandezas que o original punha na ntuple
  // (hits nas camaras, energia nos calorimetros, tempos nos hodoscopios),
  // guardadas no RunAction para o resultados.json.
  //
  EventRecord record;
  record.event = event->GetEventID();
  auto primary = event->GetPrimaryVertex(0)->GetPrimary(0);
  record.particle = primary->GetG4code()->GetParticleName();
  record.momentum = primary->GetTotalMomentum();

  // Drift chambers hits
  for (G4int iDet = 0; iDet < kDim; ++iDet) {
    auto hc = GetHC(event, fDriftHCID[iDet]);
    if (!hc) return;
    (iDet == 0 ? record.dc1Hits : record.dc2Hits) = static_cast<G4int>(hc->GetSize());
  }

  // Em/Had Calorimeters hits
  array<G4int, kDim> totalCalHit = {{0, 0}};
  array<G4double, kDim> totalCalEdep = {{0., 0.}};

  for (G4int iDet = 0; iDet < kDim; ++iDet) {
    auto hc = GetHC(event, fCalHCID[iDet]);
    if (!hc) return;

    for (unsigned long i = 0; i < hc->GetSize(); ++i) {
      G4double edep = 0.;
      // The EM and Had calorimeter hits are of different types
      if (iDet == 0) {
        auto hit = static_cast<EmCalorimeterHit*>(hc->GetHit(i));
        edep = hit->GetEdep();
      }
      else {
        auto hit = static_cast<HadCalorimeterHit*>(hc->GetHit(i));
        edep = hit->GetEdep();
      }
      if (edep > 0.) {
        totalCalHit[iDet]++;
        totalCalEdep[iDet] += edep;
      }
    }
  }
  record.emEdep = totalCalEdep[0];
  record.hadEdep = totalCalEdep[1];
  record.emCells = totalCalHit[0];
  record.hadCells = totalCalHit[1];

  // Hodoscopes hits: o tempo mais cedo de cada hodoscopio (no original a
  // ntuple guardava o tempo do ultimo acerto lido)
  for (G4int iDet = 0; iDet < kDim; ++iDet) {
    auto hc = GetHC(event, fHodHCID[iDet]);
    if (!hc) return;
    G4double earliest = -1.;
    for (unsigned int i = 0; i < hc->GetSize(); ++i) {
      auto hit = static_cast<HodoscopeHit*>(hc->GetHit(i));
      if (earliest < 0. || hit->GetTime() < earliest) earliest = hit->GetTime();
    }
    (iDet == 0 ? record.time1 : record.time2) = earliest;
  }

  if (fRunAction) fRunAction->AddEvent(record);

  //
  // Print diagnostics
  //

  auto printModulo = G4RunManager::GetRunManager()->GetPrintProgress();
  if (printModulo == 0 || event->GetEventID() % printModulo != 0) return;

  G4cout << G4endl << ">>> Event " << event->GetEventID()
         << " >>> Simulation truth : " << primary->GetG4code()->GetParticleName() << " "
         << primary->GetMomentum() << G4endl;

  // Hodoscopes
  for (G4int iDet = 0; iDet < kDim; ++iDet) {
    auto hc = GetHC(event, fHodHCID[iDet]);
    if (!hc) return;
    G4cout << "Hodoscope " << iDet + 1 << " has " << hc->GetSize() << " hits." << G4endl;
    for (unsigned int i = 0; i < hc->GetSize(); ++i) {
      hc->GetHit(i)->Print();
    }
  }

  // Drift chambers
  for (G4int iDet = 0; iDet < kDim; ++iDet) {
    auto hc = GetHC(event, fDriftHCID[iDet]);
    if (!hc) return;
    G4cout << "Drift Chamber " << iDet + 1 << " has " << hc->GetSize() << " hits." << G4endl;
    for (auto layer = 0; layer < kNofChambers; ++layer) {
      for (unsigned int i = 0; i < hc->GetSize(); i++) {
        auto hit = static_cast<DriftChamberHit*>(hc->GetHit(i));
        if (hit->GetLayerID() == layer) hit->Print();
      }
    }
  }

  // Calorimeters
  array<G4String, kDim> calName = {{"EM", "Hadron"}};
  for (G4int iDet = 0; iDet < kDim; ++iDet) {
    G4cout << calName[iDet] << " Calorimeter has " << totalCalHit[iDet] << " hits."
           << " Total Edep is " << totalCalEdep[iDet] / MeV << " (MeV)" << G4endl;
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace B5
