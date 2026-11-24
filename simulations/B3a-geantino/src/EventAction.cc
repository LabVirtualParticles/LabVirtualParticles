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
/// \file B3/B3a/src/EventAction.cc
/// \brief Implementation of the B3a::EventAction class
///
/// Modificado pelo Geantino Labs (IFPR), nov/2026: nos eventos "bons"
/// (mesmo criterio do original: 2 cristais acima de 500 keV), registra a
/// linha de resposta entre os dois cristais, lida do scorer
/// "crystal/edepRC" (ver CrystalScorer.hh). Tambem manda para o espectro a
/// energia de cada cristal atingido, em todos os eventos. A contagem de
/// eventos bons e a dose seguem exatamente o codigo original.

#include "EventAction.hh"

#include "CrystalScorer.hh"
#include "RunAction.hh"

#include "G4Event.hh"
#include "G4HCofThisEvent.hh"
#include "G4SDManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4THitsMap.hh"

#include <vector>

namespace B3a
{

EventAction::EventAction(RunAction* runAction) : fRunAction(runAction) {}

void EventAction::BeginOfEventAction(const G4Event* /*evt*/) {}

void EventAction::EndOfEventAction(const G4Event* evt)
{
  // Hits collections
  //
  G4HCofThisEvent* HCE = evt->GetHCofThisEvent();
  if (!HCE) return;

  // Get hits collections IDs
  if (fCollID_cryst < 0) {
    G4SDManager* SDMan = G4SDManager::GetSDMpointer();
    fCollID_cryst = SDMan->GetCollectionID("crystal/edep");
    fCollID_patient = SDMan->GetCollectionID("patient/dose");
    fCollID_crystRC = SDMan->GetCollectionID("crystal/edepRC");
  }

  // Energy in crystals : identify 'good events'
  //
  const G4double eThreshold = 500 * keV;
  G4int nbOfFired = 0;

  auto evtMap = static_cast<G4THitsMap<G4double>*>(HCE->GetHC(fCollID_cryst));

  for (auto& mapElement : (*evtMap->GetMap())) {
    auto edep = *(mapElement.second);
    if (edep > eThreshold) ++nbOfFired;
  }
  // Geantino Labs: espectro de energia por cristal individual
  auto rcMap = static_cast<G4THitsMap<G4double>*>(HCE->GetHC(fCollID_crystRC));
  for (auto& mapElement : (*rcMap->GetMap())) {
    fRunAction->AddCrystalHit(*(mapElement.second));
  }

  if (nbOfFired == 2) {
    fRunAction->CountEvent();

    // Geantino Labs: linha de resposta entre os dois cristais
    std::vector<std::pair<G4int, G4double>> fired;
    for (auto& mapElement : (*rcMap->GetMap())) {
      auto edep = *(mapElement.second);
      if (edep > eThreshold) fired.emplace_back(mapElement.first, edep);
    }
    G4ThreeVector c1, c2;
    if (fired.size() == 2 && Geantino::CrystalScorer::CentreOf(fired[0].first, c1)
        && Geantino::CrystalScorer::CentreOf(fired[1].first, c2))
    {
      LineOfResponse lor;
      lor.event = evt->GetEventID();
      lor.p1 = c1;
      lor.p2 = c2;
      lor.e1 = fired[0].second;
      lor.e2 = fired[1].second;
      fRunAction->AddLineOfResponse(lor);
    }
  }

  // Dose deposit in patient
  //
  G4double dose = 0.;

  evtMap = static_cast<G4THitsMap<G4double>*>(HCE->GetHC(fCollID_patient));

  for (auto& mapElement : (*evtMap->GetMap())) {
    dose += *(mapElement.second);
  }
  if (dose > 0.) fRunAction->SumDose(dose);
}

}  // namespace B3a
