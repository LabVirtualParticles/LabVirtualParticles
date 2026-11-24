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
/// \file geantinoB3a.cc
/// \brief Programa principal do exemplo B3a adaptado para o Geantino Labs
///
/// Baseado em examples/basic/B3/B3a/exampleB3a.cc, da Colaboracao Geant4.
/// Modificado pelo Geantino Labs (IFPR) em nov/2026 para rodar so em modo
/// batch, num servidor sem tela, disparado pelo backend do site:
///   - sem G4UIExecutive / G4VisExecutive (nada de parte grafica);
///   - sem o G4TScoreNtupleWriter (nao gera scoring.root);
///   - run manager sequencial (um processo por simulacao; o backend ja
///     isola cada execucao num diretorio proprio).
/// A fisica, a geometria e os detectores sao os do exemplo original.

#include "ActionInitialization.hh"
#include "DetectorConstruction.hh"
#include "PhysicsList.hh"

#include "G4RunManagerFactory.hh"
#include "G4SteppingVerbose.hh"
#include "G4Types.hh"
#include "G4UImanager.hh"
#include "globals.hh"

int main(int argc, char** argv)
{
  if (argc < 2) {
    G4cerr << "Uso: " << argv[0] << " macro.mac" << G4endl
           << "Esta versao do B3a roda so em modo batch (sem interface grafica)." << G4endl;
    return 1;
  }

  // use G4SteppingVerboseWithUnits
  G4int precision = 4;
  G4SteppingVerbose::UseBestUnit(precision);

  // Sequencial de proposito: TrajectoryRecorder e a lista de linhas de
  // resposta (RunAction) ficam num lugar so, sem precisar juntar threads.
  auto runManager = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Serial);

  runManager->SetUserInitialization(new B3::DetectorConstruction);
  runManager->SetUserInitialization(new B3::PhysicsList);
  runManager->SetUserInitialization(new B3a::ActionInitialization());

  auto UImanager = G4UImanager::GetUIpointer();
  UImanager->ApplyCommand(G4String("/control/execute ") + argv[1]);

  delete runManager;
  return 0;
}
