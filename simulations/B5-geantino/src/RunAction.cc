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
/// \file B5/src/RunAction.cc
/// \brief Implementation of the B5::RunAction class
///
/// Modificado pelo Geantino Labs (IFPR), nov/2026 — ver o .hh.

#include "RunAction.hh"

#include "TrajectoryRecorder.hh"

#include "G4GDMLParser.hh"
#include "G4Run.hh"
#include "G4SystemOfUnits.hh"
#include "G4TransportationManager.hh"
#include "G4VPhysicalVolume.hh"

#include <cstdio>
#include <fstream>

namespace B5
{

void RunAction::BeginOfRunAction(const G4Run* /*run*/)
{
  Geantino::TrajectoryRecorder::Instance()->Clear();
  fEvents.clear();

  // Geometria em GDML para o visualizador 3D (nao ha comando de macro para
  // isso). Gravada aqui, depois de /B5/detector/armAngle ja ter girado o
  // segundo braco. O Write nao sobrescreve arquivo existente.
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
  auto recorder = Geantino::TrajectoryRecorder::Instance();
  recorder->WriteJSON("trajetorias.json");
  WriteResultsJSON(run);
  G4cout << "[Geantino] " << run->GetNumberOfEvent() << " eventos; " << recorder->PointCount()
         << " pontos de trajetoria" << (recorder->IsTruncated() ? " (limite atingido)" : "")
         << ". Arquivos: geometria.gdml, trajetorias.json, resultados.json" << G4endl;
}

void RunAction::WriteResultsJSON(const G4Run* run) const
{
  std::ofstream out("resultados.json");
  out.precision(8);
  out << "{\"n_events\": " << run->GetNumberOfEvent() << ", \"trajectories_truncated\": "
      << (Geantino::TrajectoryRecorder::Instance()->IsTruncated() ? "true" : "false")
      << ", \"events\": [";
  for (std::size_t i = 0; i < fEvents.size(); ++i) {
    const auto& e = fEvents[i];
    out << "{\"event\": " << e.event << ", \"particle\": \"" << e.particle << "\""
        << ", \"momentum_MeV\": " << e.momentum / MeV << ", \"dc1_hits\": " << e.dc1Hits
        << ", \"dc2_hits\": " << e.dc2Hits << ", \"em_edep_MeV\": " << e.emEdep / MeV
        << ", \"had_edep_MeV\": " << e.hadEdep / MeV << ", \"em_cells\": " << e.emCells
        << ", \"had_cells\": " << e.hadCells << ", \"t1_ns\": ";
    if (e.time1 >= 0.) out << e.time1 / ns; else out << "null";
    out << ", \"t2_ns\": ";
    if (e.time2 >= 0.) out << e.time2 / ns; else out << "null";
    out << "}" << (i + 1 < fEvents.size() ? ", " : "");
  }
  out << "]}";
}

}  // namespace B5
