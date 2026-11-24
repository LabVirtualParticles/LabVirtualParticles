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
/// \file B3/B3a/src/RunAction.cc
/// \brief Implementation of the B3a::RunAction class
///
/// Modificado pelo Geantino Labs (IFPR), nov/2026 — ver o .hh.

#include "RunAction.hh"

#include "PrimaryGeneratorAction.hh"
#include "TrajectoryRecorder.hh"

#include "G4AccumulableManager.hh"
#include "G4GDMLParser.hh"
#include "G4ParticleGun.hh"
#include "G4Run.hh"
#include "G4RunManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4TransportationManager.hh"
#include "G4UnitsTable.hh"
#include "G4VPhysicalVolume.hh"

#include <algorithm>
#include <cstdio>
#include <fstream>

using namespace B3;

namespace B3a
{

RunAction::RunAction()
{
  // add new units for dose
  //
  const G4double milligray = 1.e-3 * gray;
  const G4double microgray = 1.e-6 * gray;
  const G4double nanogray = 1.e-9 * gray;
  const G4double picogray = 1.e-12 * gray;

  new G4UnitDefinition("milligray", "milliGy", "Dose", milligray);
  new G4UnitDefinition("microgray", "microGy", "Dose", microgray);
  new G4UnitDefinition("nanogray", "nanoGy", "Dose", nanogray);
  new G4UnitDefinition("picogray", "picoGy", "Dose", picogray);

  // Register accumulable to the accumulable manager
  G4AccumulableManager* accumulableManager = G4AccumulableManager::Instance();
  accumulableManager->Register(fGoodEvents);
  accumulableManager->Register(fSumDose);
}

void RunAction::BeginOfRunAction(const G4Run* run)
{
  G4cout << "### Run " << run->GetRunID() << " start." << G4endl;

  // reset accumulables to their initial values
  G4AccumulableManager* accumulableManager = G4AccumulableManager::Instance();
  accumulableManager->Reset();

  // inform the runManager to save random number seed
  G4RunManager::GetRunManager()->SetRandomNumberStore(false);

  // Geantino Labs: zera o que e gravado para o site
  Geantino::TrajectoryRecorder::Instance()->Clear();
  fLines.clear();
  std::fill(fSpectrum.begin(), fSpectrum.end(), 0);
  fSpectrumOverflow = 0;

  // Geometria em GDML para o visualizador 3D. Nao ha comando de macro
  // para isso: precisa ser feito aqui, com o G4GDMLParser. O Write nao
  // sobrescreve arquivo existente, por isso o remove antes.
  auto worldVolume = G4TransportationManager::GetTransportationManager()
                       ->GetNavigatorForTracking()
                       ->GetWorldVolume();
  if (worldVolume) {
    std::remove("geometria.gdml");
    G4GDMLParser parser;
    parser.Write("geometria.gdml", worldVolume);
  }
}

void RunAction::EndOfRunAction(const G4Run* run)
{
  G4int nofEvents = run->GetNumberOfEvent();
  if (nofEvents == 0) return;

  // Merge accumulables
  G4AccumulableManager* accumulableManager = G4AccumulableManager::Instance();
  accumulableManager->Merge();

  // Run conditions
  //  note: There is no primary generator action object for "master"
  //        run manager for multi-threaded mode.
  const auto generatorAction = static_cast<const PrimaryGeneratorAction*>(
    G4RunManager::GetRunManager()->GetUserPrimaryGeneratorAction());
  G4String partName;
  if (generatorAction) {
    G4ParticleDefinition* particle = generatorAction->GetParticleGun()->GetParticleDefinition();
    partName = particle->GetParticleName();
  }

  // Print results
  //
  if (IsMaster()) {
    G4cout << G4endl << "--------------------End of Global Run-----------------------" << G4endl
           << "  The run was " << nofEvents << " events ";
  }
  else {
    G4cout << G4endl << "--------------------End of Local Run------------------------" << G4endl
           << "  The run was " << nofEvents << " " << partName;
  }
  G4cout << "; Nb of 'good' e+ annihilations: " << fGoodEvents.GetValue() << G4endl
         << " Total dose in patient : " << G4BestUnit(fSumDose.GetValue(), "Dose") << G4endl
         << "------------------------------------------------------------" << G4endl << G4endl;

  // Geantino Labs: arquivos para o site
  auto recorder = Geantino::TrajectoryRecorder::Instance();
  recorder->WriteJSON("trajetorias.json");
  WriteResultsJSON(run);
  G4cout << "[Geantino] " << nofEvents << " eventos; " << recorder->PointCount()
         << " pontos de trajetoria" << (recorder->IsTruncated() ? " (limite atingido)" : "")
         << "; " << fLines.size() << " linhas de resposta. Arquivos: geometria.gdml, "
         << "trajetorias.json, resultados.json" << G4endl;
}

void RunAction::AddCrystalHit(G4double edep)
{
  const auto bin = static_cast<G4int>(edep / keV / kSpectrumBinkeV);
  if (bin >= 0 && bin < kSpectrumBins) {
    ++fSpectrum[bin];
  }
  else if (bin >= kSpectrumBins) {
    ++fSpectrumOverflow;
  }
}

void RunAction::WriteResultsJSON(const G4Run* run) const
{
  const auto generatorAction = static_cast<const PrimaryGeneratorAction*>(
    G4RunManager::GetRunManager()->GetUserPrimaryGeneratorAction());
  G4String partName = "desconhecida";
  if (generatorAction) {
    partName = generatorAction->GetParticleGun()->GetParticleDefinition()->GetParticleName();
  }

  const G4int nofEvents = run->GetNumberOfEvent();
  const G4int good = fGoodEvents.GetValue();

  std::ofstream out("resultados.json");
  out.precision(8);
  out << "{\"n_events\": " << nofEvents << ", \"source_particle\": \"" << partName << "\""
      << ", \"good_events\": " << good
      << ", \"good_fraction\": " << (nofEvents > 0 ? G4double(good) / nofEvents : 0.)
      << ", \"dose_Gy\": " << fSumDose.GetValue() / gray
      << ", \"energy_threshold_keV\": 500"
      << ", \"trajectories_truncated\": "
      << (Geantino::TrajectoryRecorder::Instance()->IsTruncated() ? "true" : "false")
      << ", \"lines_of_response\": [";
  for (std::size_t i = 0; i < fLines.size(); ++i) {
    const auto& l = fLines[i];
    out << "{\"event\": " << l.event << ", \"points\": [[" << l.p1.x() / cm << ", "
        << l.p1.y() / cm << ", " << l.p1.z() / cm << "], [" << l.p2.x() / cm << ", "
        << l.p2.y() / cm << ", " << l.p2.z() / cm << "]], \"edep_keV\": [" << l.e1 / keV
        << ", " << l.e2 / keV << "]}";
    if (i + 1 < fLines.size()) out << ", ";
  }
  out << "], \"crystal_spectrum\": {\"bin_keV\": " << kSpectrumBinkeV
      << ", \"max_keV\": " << kSpectrumBinkeV * kSpectrumBins << ", \"overflow\": " << fSpectrumOverflow
      << ", \"counts\": [";
  for (std::size_t i = 0; i < fSpectrum.size(); ++i) {
    out << fSpectrum[i] << (i + 1 < fSpectrum.size() ? ", " : "");
  }
  out << "]}}";
}

}  // namespace B3a
