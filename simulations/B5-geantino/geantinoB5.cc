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
/// \file geantinoB5.cc
/// \brief Programa principal do exemplo B5 adaptado para o Geantino Labs
///
/// Baseado em examples/basic/B5/exampleB5.cc, da Colaboracao Geant4.
/// Modificado pelo Geantino Labs (IFPR) em nov/2026 para rodar so em modo
/// batch, num servidor sem tela, disparado pelo backend do site:
///   - sem G4UIExecutive / G4VisExecutive (nada de parte grafica);
///   - run manager sequencial (um processo por simulacao);
///   - sem arquivos ROOT (ver RunAction: grava JSON para o site).
/// A fisica (FTFP_BERT + limitador de passo), a geometria e os detectores
/// sao os do exemplo original.

#include "ActionInitialization.hh"
#include "DetectorConstruction.hh"
#include "FTFP_BERT.hh"

#include "G4RunManagerFactory.hh"
#include "G4StepLimiterPhysics.hh"
#include "G4SteppingVerbose.hh"
#include "G4UImanager.hh"
#include "globals.hh"

int main(int argc, char** argv)
{
  if (argc < 2) {
    G4cerr << "Uso: " << argv[0] << " macro.mac" << G4endl
           << "Esta versao do B5 roda so em modo batch (sem interface grafica)." << G4endl;
    return 1;
  }

  // Use G4SteppingVerboseWithUnits
  G4int precision = 4;
  G4SteppingVerbose::UseBestUnit(precision);

  auto runManager = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Serial);

  runManager->SetUserInitialization(new B5::DetectorConstruction);

  auto physicsList = new FTFP_BERT;
  physicsList->RegisterPhysics(new G4StepLimiterPhysics());
  runManager->SetUserInitialization(physicsList);

  runManager->SetUserInitialization(new B5::ActionInitialization());

  auto UImanager = G4UImanager::GetUIpointer();
  UImanager->ApplyCommand(G4String("/control/execute ") + argv[1]);

  delete runManager;
  return 0;
}
